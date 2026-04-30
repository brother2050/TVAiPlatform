import sys
import os
import uuid
import threading
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from shared.config import load_config
from shared.redis_client import cache_set, cache_get

from services.compositor.models import ComposeRequest
from services.compositor.video_builder import compose_segment


# 任务状态存储（内存 + Redis 双写）
_tasks: dict = {}


def _update_task(task_id: str, **kwargs):
    _tasks[task_id].update(kwargs)
    cache_set(f"compose:task:{task_id}", _tasks[task_id], expire=7200)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    print(f"[CompositorService] 启动完成")
    print(f"  端口: {cfg['services']['compositor_service']['port']}")
    yield
    print("[CompositorService] 关闭")


app = FastAPI(
    title="文章转视频 - 视频合成服务",
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


@app.get("/health")
def health():
    import subprocess
    ffmpeg_version = "unknown"
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        ffmpeg_version = result.stdout.split("\n")[0] if result.stdout else "unknown"
    except Exception:
        pass

    disk_free = 0
    try:
        st = os.statvfs(".")
        disk_free = round(st.f_bavail * st.f_frsize / (1024 ** 3), 1)
    except Exception:
        pass

    return {
        "status": "healthy",
        "service": "compositor_service",
        "ffmpeg_version": ffmpeg_version,
        "disk_free_gb": disk_free,
    }


@app.post("/api/compositor/segment")
def compose_segment_api(body: ComposeRequest):
    if not body.shots:
        raise HTTPException(400, "没有分镜数据")

    task_id = f"compose_{uuid.uuid4().hex[:12]}"
    ts = datetime.now(timezone.utc).isoformat()

    # 初始化任务状态
    _tasks[task_id] = {
        "task_id": task_id,
        "segment_id": body.segment_id,
        "status": "processing",
        "progress_percent": 0,
        "current_step": "初始化",
        "started_at": ts,
        "video_path": "",
        "duration": 0,
        "resolution": "",
        "file_size_mb": 0,
    }

    # 准备分镜数据
    shots_data = [s.model_dump() for s in body.shots]

    # 获取输出路径
    from shared.config import get_config
    from shared.storage import get_storage
    cfg = get_config()
    storage = get_storage()

    # 找到项目 ID（通过分镜 → 段落 → 项目 的关联）
    # 这里简化：直接用 segment_id 构造路径
    output_path = str(storage.get_segment_path("_auto", body.segment_id) / "video.mp4")

    # 构建配置
    subtitle_config = body.subtitle.model_dump() if body.subtitle else {"enabled": True}
    transition_config = body.transition.model_dump() if body.transition else {"type": "fade", "duration": 0.5}
    title_config = body.title.model_dump() if body.title else {"enabled": False}
    bgm_config = body.background_music.model_dump() if body.background_music else None

    def progress_cb(step_name, percent):
        _update_task(task_id, current_step=step_name, progress_percent=percent)

    try:
        result = compose_segment(
            segment_id=body.segment_id,
            shots=shots_data,
            output_path=output_path,
            output_format=body.output_format,
            subtitle_config=subtitle_config,
            transition_config=transition_config,
            title_config=title_config,
            bgm_config=bgm_config,
            progress_callback=progress_cb,
        )

        _update_task(
            task_id,
            status="completed",
            progress_percent=100,
            current_step="完成",
            video_path=result["video_path"],
            duration=result["duration"],
            resolution=result["resolution"],
            file_size_mb=result["file_size_mb"],
        )

        return {
            "task_id": task_id,
            **result,
        }

    except Exception as e:
        _update_task(
            task_id,
            status="failed",
            current_step=f"失败: {str(e)}",
        )
        raise HTTPException(500, f"视频合成失败: {str(e)}")


@app.post("/api/compositor/segment/async")
def compose_segment_async(body: ComposeRequest):
    """异步版本：提交后立即返回 task_id，后台执行"""
    if not body.shots:
        raise HTTPException(400, "没有分镜数据")

    task_id = f"compose_{uuid.uuid4().hex[:12]}"
    ts = datetime.now(timezone.utc).isoformat()

    _tasks[task_id] = {
        "task_id": task_id,
        "segment_id": body.segment_id,
        "status": "queued",
        "progress_percent": 0,
        "current_step": "排队中",
        "started_at": ts,
    }

    def run():
        # 复用同步接口的逻辑
        try:
            compose_segment_api(body)
        except Exception:
            pass

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return {"task_id": task_id, "status": "queued"}


@app.get("/api/compositor/status/{task_id}")
def get_compose_status(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        task = cache_get(f"compose:task:{task_id}")
    if not task:
        raise HTTPException(404, "任务不存在")
    return task


if __name__ == "__main__":
    import uvicorn
    cfg = load_config()
    svc = cfg["services"]["compositor_service"]
    uvicorn.run(
        "services.compositor.app:app",
        host=svc["host"],
        port=svc["port"],
        reload=True,
    )
