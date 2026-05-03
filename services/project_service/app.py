import sys
import os
import json
import urllib.request

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from shared.config import load_config
from shared.database import get_db
from shared.storage import get_storage
from shared.redis_client import get_redis

from services.project_service.routers import projects, segments, shots, batch

# 配置 Jinja2 模板
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    cfg = load_config()
    db = get_db()
    db.init_tables()
    get_storage()
    redis_ok = get_redis()
    print(f"[ProjectService] 启动完成")
    print(f"  数据库: {cfg['database']['sqlite_path']}")
    print(f"  存储: {cfg['storage']['local_path']}")
    print(f"  Redis: {'已连接' if redis_ok else '未连接（可选）'}")
    yield
    print("[ProjectService] 关闭")


app = FastAPI(
    title="文章转视频 - 项目管理服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router)
app.include_router(segments.router)
app.include_router(shots.router)
app.include_router(batch.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "project_service"}


# ==================== Web 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def ui_index(request: Request):
    """项目列表页面"""
    from services.project_service.db import list_projects, get_segments_by_project

    all_projects, _ = list_projects(page=1, page_size=100)
    projects_list = []
    for p in all_projects:
        segs = get_segments_by_project(p["id"])
        completed = sum(1 for s in segs if s.get("status") == "completed")
        projects_list.append({
            "id": p["id"],
            "name": p.get("name", "未命名"),
            "split_mode": p.get("split_mode", "auto"),
            "segment_count": len(segs),
            "completed_count": completed,
            "progress": round(completed / len(segs) * 100) if segs else 0,
            "created_at": p.get("created_at", "")[:16],
        })
    projects_list.sort(key=lambda x: x["created_at"], reverse=True)
    return templates.TemplateResponse("projects.html", {"request": request, "projects": projects_list})


@app.get("/ui/projects/new", response_class=HTMLResponse)
async def ui_new_project(request: Request):
    """新建项目页面"""
    return templates.TemplateResponse("project_new.html", {"request": request})


@app.post("/ui/projects/new")
async def ui_create_project(
    request: Request,
    name: str = Form(...),
    split_mode: str = Form(...),
    source_text: str = Form(...),
    style_hint: str = Form(""),
):
    """创建项目并跳转"""
    from services.project_service.db import create_project, update_project
    from services.project_service.routers.segments import split_text_to_segments

    project = create_project(
        name=name,
        author="",
        source_text_path="",
        split_mode=split_mode,
        style_hint=style_hint,
    )
    pid = project["id"]

    # 保存原文到 storage
    storage = get_storage()
    text_path = storage.save_text(pid, source_text)
    update_project(pid, source_text_path=text_path)

    # 拆分段落
    segs = split_text_to_segments(source_text, split_mode)
    for seg_data in segs:
        segments.create_segment(pid, seg_data)

    return RedirectResponse(url=f"/ui/projects/{pid}", status_code=303)


@app.get("/ui/projects/{project_id}", response_class=HTMLResponse)
async def ui_project_detail(request: Request, project_id: str):
    """项目详情页面"""
    from services.project_service.db import get_project, get_segments_by_project, get_shots_by_segment

    project = get_project(project_id)
    if not project:
        return HTMLResponse("项目不存在", status_code=404)

    segs = get_segments_by_project(project_id)
    segments_list = []
    for seg in segs:
        shots_data = get_shots_by_segment(seg["id"])
        segments_list.append({
            "id": seg["id"],
            "segment_index": seg.get("segment_index", 0),
            "title": seg.get("title", ""),
            "content": seg.get("content", ""),
            "summary": seg.get("summary", ""),
            "status": seg.get("status", "pending"),
            "video_path": seg.get("video_path", ""),
            "shots": [dict(s) for s in shots_data],
        })
    segments_list.sort(key=lambda x: x["segment_index"])

    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "project": project,
        "segments": segments_list,
    })


@app.post("/ui/projects/{project_id}/delete")
async def ui_delete_project(project_id: str):
    """删除项目"""
    from services.project_service.db import delete_project, delete_segments_by_project

    delete_segments_by_project(project_id)
    delete_project(project_id)
    return RedirectResponse(url="/", status_code=303)


@app.get("/ui/shots/{shot_id}", response_class=HTMLResponse)
async def ui_shot_detail(request: Request, shot_id: str):
    """分镜详情页面"""
    from services.project_service.db import get_shot, get_segments_by_project

    shot = get_shot(shot_id)
    if not shot:
        return HTMLResponse("分镜不存在", status_code=404)

    # 查找所属项目ID
    for p in []:
        segs = get_segments_by_project(p["id"])
        for seg in segs:
            if seg["id"] == shot["segment_id"]:
                shot["project_id"] = p["id"]
                break

    # 直接查询
    db = get_db()
    seg = db.fetchone("SELECT project_id FROM segments WHERE id=?", (shot["segment_id"],))
    shot["project_id"] = seg["project_id"] if seg else ""

    return templates.TemplateResponse("shot_detail.html", {
        "request": request,
        "shot": shot,
    })


@app.post("/ui/shots/{shot_id}/regenerate")
async def ui_regenerate_shot(shot_id: str):
    """原词重生成图片"""
    from services.project_service.db import get_shot, update_shot, get_latest_version_number, create_shot_version

    shot = get_shot(shot_id)
    if not shot:
        return HTMLResponse("分镜不存在", status_code=404)

    prompt = shot.get("prompt", "")
    try:
        req_data = json.dumps({
            "prompt": prompt,
            "negative_prompt": shot.get("negative_prompt", ""),
            "width": 1024, "height": 576, "steps": 30, "seed": -1
        }).encode()
        req = urllib.request.Request(
            "http://localhost:8188/api/prompt",
            data=req_data,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            image_url = result.get("image_url", "")
            if image_url:
                new_version = get_latest_version_number(shot_id) + 1
                create_shot_version(shot_id, new_version, image_url, prompt, shot.get("negative_prompt", ""), "regenerate")
                update_shot(shot_id, image_path=image_url, current_version=new_version, status="rendered")
    except Exception:
        pass

    return RedirectResponse(url=f"/ui/shots/{shot_id}", status_code=303)


@app.post("/ui/shots/{shot_id}/regenerate_custom")
async def ui_regenerate_custom(
    request: Request,
    shot_id: str,
    new_prompt: str = Form(""),
    new_description: str = Form(""),
):
    """修改提示词后重生成"""
    from services.project_service.db import get_shot, update_shot, get_latest_version_number, create_shot_version

    shot = get_shot(shot_id)
    if not shot:
        return HTMLResponse("分镜不存在", status_code=404)

    prompt = new_prompt or shot.get("prompt", "")
    if new_description and not new_prompt:
        prompt = f"{new_description}, detailed, cinematic"

    update_shot(shot_id, prompt=prompt)

    try:
        req_data = json.dumps({
            "prompt": prompt,
            "negative_prompt": shot.get("negative_prompt", ""),
            "width": 1024, "height": 576, "steps": 30, "seed": -1
        }).encode()
        req = urllib.request.Request(
            "http://localhost:8188/api/prompt",
            data=req_data,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            image_url = result.get("image_url", "")
            if image_url:
                new_version = get_latest_version_number(shot_id) + 1
                create_shot_version(shot_id, new_version, image_url, prompt, shot.get("negative_prompt", ""), "custom")
                update_shot(shot_id, image_path=image_url, current_version=new_version, status="rendered")
    except Exception:
        pass

    return RedirectResponse(url=f"/ui/shots/{shot_id}", status_code=303)


@app.post("/ui/segments/{segment_id}/render")
async def ui_render_segment(segment_id: str):
    """渲染段落"""
    from services.project_service.db import update_segment

    update_segment(segment_id, status="rendered")
    db = get_db()
    seg = db.fetchone("SELECT project_id FROM segments WHERE id=?", (segment_id,))
    pid = seg["project_id"] if seg else ""
    return RedirectResponse(url=f"/ui/projects/{pid}", status_code=303)


@app.post("/ui/segments/{segment_id}/confirm")
async def ui_confirm_segment(segment_id: str):
    """确认并合成"""
    from services.project_service.db import get_segment, update_segment, get_shots_by_segment

    seg = get_segment(segment_id)
    if not seg:
        return HTMLResponse("段落不存在", status_code=404)

    shots = get_shots_by_segment(segment_id)
    compose_shots = []
    for shot in shots:
        compose_shots.append({
            "shot_id": shot["id"],
            "shot_index": shot.get("shot_index", 0),
            "image_path": shot.get("image_path", ""),
            "audio_path": shot.get("audio_path", ""),
            "audio_duration": shot.get("audio_duration", 5.0),
            "dialogue": shot.get("dialogue", ""),
            "narrator_text": shot.get("narrator_text", ""),
            "speaker": shot.get("speaker", ""),
        })

    compose_body = {
        "segment_id": segment_id,
        "shots": compose_shots,
        "output_format": "horizontal_16_9",
        "subtitle": {"enabled": True, "font_size": 24},
        "transition": {"type": "fade", "duration": 0.5},
        "title": {"enabled": False},
    }

    try:
        req_data = json.dumps(compose_body).encode()
        req = urllib.request.Request(
            "http://localhost:5004/api/compositor/segment",
            data=req_data,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode())
            update_segment(segment_id,
                video_path=result.get("video_path", ""),
                video_duration=result.get("duration", 0),
                status="completed"
            )
    except Exception:
        update_segment(segment_id, status="rendered")

    return RedirectResponse(url=f"/ui/projects/{seg['project_id']}", status_code=303)


@app.post("/ui/segments/{segment_id}/recompose")
async def ui_recompose_segment(segment_id: str):
    """重新合成"""
    from services.project_service.db import get_segment, update_segment

    seg = get_segment(segment_id)
    if not seg:
        return HTMLResponse("段落不存在", status_code=404)

    update_segment(segment_id, status="rendered", pending_recompose=True)
    return RedirectResponse(url=f"/ui/projects/{seg['project_id']}", status_code=303)


if __name__ == "__main__":
    import uvicorn
    cfg = load_config()
    svc = cfg["services"]["project_service"]
    uvicorn.run(
        "services.project_service.app:app",
        host=svc["host"],
        port=svc["port"],
        reload=True,
    )
