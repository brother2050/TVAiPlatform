from fastapi import APIRouter, HTTPException, Query
from services.project_service.models import ProjectCreate, ProjectUpdate, ProjectResponse
from services.project_service import db
from shared.storage import get_storage

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
def create_project(body: ProjectCreate):
    storage = get_storage()
    project = db.create_project(
        name=body.name,
        author=body.author,
        source_text_path="",
        split_mode=body.split_mode,
        style_hint=body.style_hint,
    )
    if body.source_text:
        path = storage.save_text(f"projects/{project['id']}/source/full_text.txt", body.source_text)
        db.update_project(project["id"], source_text_path=path)
        project["source_text_path"] = path
    return _to_response(project)


@router.get("")
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
):
    rows, total = db.list_projects(page, page_size, status)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_to_response(r) for r in rows],
    }


@router.get("/{project_id}", response_model=dict)
def get_project(project_id: str):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "项目不存在")

    segments = db.get_segments_by_project(project_id)
    seg_list = []
    for seg in segments:
        shots = db.get_shots_by_segment(seg["id"])
        seg_dict = dict(seg)
        seg_dict["shots"] = [dict(s) for s in shots]
        seg_dict["pending_recompose"] = bool(seg["pending_recompose"])
        seg_list.append(seg_dict)

    total_segs = len(segments)
    completed_segs = sum(1 for s in segments if s["status"] == "completed")
    progress = int(completed_segs / total_segs * 100) if total_segs > 0 else 0

    result = dict(project)
    result["segments"] = seg_list
    result["progress_percent"] = progress
    return result


@router.delete("/{project_id}")
def delete_project(project_id: str):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    db.delete_project(project_id)
    get_storage().delete_project(project_id)
    return {"message": "项目已删除", "project_id": project_id}


def _to_response(p: dict) -> dict:
    return {
        "id": p["id"],
        "name": p["name"],
        "author": p.get("author", ""),
        "split_mode": p.get("split_mode", "auto"),
        "style_hint": p.get("style_hint", ""),
        "status": p["status"],
        "total_segments": p.get("total_segments", 0),
        "completed_segments": p.get("completed_segments", 0),
        "created_at": p["created_at"],
        "updated_at": p["updated_at"],
    }
