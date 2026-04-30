import json
from fastapi import APIRouter, HTTPException, Query
from services.project_service.models import (
    SegmentCreate, SegmentUpdate, SegmentContentEdit,
    RecomposeParams, SegmentResponse,
)
from services.project_service import db

router = APIRouter(prefix="/api", tags=["segments"])


# ── 保存段落及其分镜 ──

@router.post("/projects/{project_id}/segments")
def create_segment(project_id: str, body: SegmentCreate):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "项目不存在")

    segment = db.create_segment(
        project_id=project_id,
        segment_index=body.segment_index,
        title=body.title,
        content=body.content,
        summary=body.summary,
    )

    shot_count = 0
    for shot_data in body.shots:
        db.create_shot(segment["id"], shot_data.model_dump())
        shot_count += 1

    db.update_segment(segment["id"], total_shots=shot_count)
    db.update_project(project_id, total_segments=project["total_segments"] + 1)

    return {
        "segment_id": segment["id"],
        "shot_count": shot_count,
        "status": "saved",
    }


# ── 查询段落详情 ──

@router.get("/segments/{segment_id}")
def get_segment(segment_id: str):
    segment = db.get_segment(segment_id)
    if not segment:
        raise HTTPException(404, "段落不存在")

    shots = db.get_shots_by_segment(segment_id)
    result = dict(segment)
    result["shots"] = [_shot_to_dict(s) for s in shots]
    result["pending_recompose"] = bool(segment["pending_recompose"])
    return result


# ── 更新段落 ──

@router.put("/segments/{segment_id}")
def update_segment(segment_id: str, body: SegmentUpdate):
    segment = db.get_segment(segment_id)
    if not segment:
        raise HTTPException(404, "段落不存在")

    updates = {}
    if body.status is not None:
        updates["status"] = body.status
    if body.video_path is not None:
        updates["video_path"] = body.video_path
    if body.video_duration is not None:
        updates["video_duration"] = body.video_duration
    if body.pending_recompose is not None:
        updates["pending_recompose"] = int(body.pending_recompose)
    if body.last_modified_field is not None:
        updates["last_modified_field"] = body.last_modified_field
    if body.rendered_shots is not None:
        updates["rendered_shots"] = body.rendered_shots
    if body.failed_shots is not None:
        updates["failed_shots"] = body.failed_shots

    if updates:
        db.update_segment(segment_id, **updates)

    # 如果段落标记为已完成，更新项目计数
    if body.status == "completed":
        project = db.get_project(segment["project_id"])
        if project:
            completed = db.fetchone_count_completed(segment["project_id"])  # type: ignore[attr-defined]
            db.update_project(segment["project_id"], completed_segments=completed)

    return {"segment_id": segment_id, "status": "updated"}


# ── 编辑段落文本 ──

@router.put("/segments/{segment_id}/content")
def edit_segment_content(segment_id: str, body: SegmentContentEdit):
    segment = db.get_segment(segment_id)
    if not segment:
        raise HTTPException(404, "段落不存在")

    # 更新段落内容
    db.update_segment(segment_id, content=body.content, status="content_modified", last_modified_field="content")

    # 将该段落下所有当前分镜标记为已废弃
    db.supersede_shots_by_segment(segment_id)

    affected = db.fetchone(  # type: ignore[attr-defined]
        "SELECT COUNT(*) as c FROM shots WHERE segment_id=? AND status='superseded'",
        (segment_id,),
    )

    return {
        "segment_id": segment_id,
        "status": "content_modified",
        "affected_shots": affected["c"] if affected else 0,
        "action_required": "regenerate_shots",
        "message": f"段落文本已修改，需要重新生成 {affected['c'] if affected else 0} 个分镜的脚本、图片和配音",
    }


# ── 确认段落所有分镜 ──

@router.put("/segments/{segment_id}/confirm")
def confirm_segment(segment_id: str):
    segment = db.get_segment(segment_id)  # type: ignore[attr-defined]
    if not segment:
        raise HTTPException(404, "段落不存在")

    db_conn = _get_db()
    ts = db.now_iso()  # type: ignore[attr-defined]
    cursor = db_conn.execute(
        "UPDATE shots SET status='confirmed', updated_at=? WHERE segment_id=? AND status='completed' AND is_current=1",
        (ts, segment_id),
    )
    db_conn.commit()

    db.update_segment(segment_id, status="confirmed")  # type: ignore[attr-defined]

    confirmed_count = db_conn.fetchone(  # type: ignore[attr-defined]
        "SELECT COUNT(*) as c FROM shots WHERE segment_id=? AND status='confirmed' AND is_current=1",
        (segment_id,),
    )

    return {
        "segment_id": segment_id,
        "confirmed_shots": confirmed_count["c"] if confirmed_count else 0,
        "status": "confirmed",
    }


# ── 查询段落的指定状态分镜 ──

@router.get("/segments/{segment_id}/shots")
def get_segment_shots(segment_id: str, status: str = Query(None)):
    segment = db.get_segment(segment_id)
    if not segment:
        raise HTTPException(404, "段落不存在")

    shots = db.get_shots_by_segment(segment_id, status)
    return {
        "segment_id": segment_id,
        "shots": [_shot_to_dict(s) for s in shots],
        "total": len(shots),
    }


# ── 更新合成参数并重新合成 ──

@router.post("/segments/{segment_id}/recompose")
def recompose_segment(segment_id: str, body: RecomposeParams):
    segment = db.get_segment(segment_id)
    if not segment:
        raise HTTPException(404, "段落不存在")

    compose_params = body.model_dump(exclude_none=True)
    db.update_segment(
        segment_id,
        pending_recompose=1,
        status="pending_recompose",
        last_modified_field="compose_params",
    )

    return {
        "segment_id": segment_id,
        "status": "pending_recompose",
        "compose_params": compose_params,
        "message": "已标记为待重新合成",
    }


def _shot_to_dict(s: dict) -> dict:
    result = dict(s)
    result["is_current"] = bool(result.get("is_current", 1))
    result["pending_image_regen"] = bool(result.get("pending_image_regen", 0))
    result["pending_audio_regen"] = bool(result.get("pending_audio_regen", 0))
    return result


def _get_db():
    from shared.database import get_db
    return get_db()


# 补充查询：已完成段落数
def _count_completed_segments(project_id: str) -> int:
    from shared.database import get_db
    db_inst = get_db()
    row = db_inst.fetchone(
        "SELECT COUNT(*) as c FROM segments WHERE project_id=? AND status='completed'",
        (project_id,),
    )
    return row["c"] if row else 0


# 给 db 模块补一个方法引用
def _patch_db():
    if not hasattr(db, "fetchone_count_completed"):
        def fetchone_count_completed(project_id):
            from shared.database import get_db
            d = get_db()
            row = d.fetchone(
                "SELECT COUNT(*) as c FROM segments WHERE project_id=? AND status='completed'",
                (project_id,),
            )
            return row["c"] if row else 0
        db.fetchone_count_completed = fetchone_count_completed  # type: ignore[attr-defined]

_patch_db()