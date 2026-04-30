from fastapi import APIRouter, HTTPException
from services.project_service.models import ProcessPendingRequest
from services.project_service import db

router = APIRouter(prefix="/api/projects", tags=["batch"])


# ── 查询项目待处理项 ──

@router.get("/{project_id}/pending")
def get_pending_items(project_id: str):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "项目不存在")

    pending_items = []

    # 待重新生成图片的分镜
    image_shots = db.get_pending_image_shots(project_id)
    for shot in image_shots:
        pending_items.append({
            "type": "image",
            "shot_id": shot["id"],
            "segment_id": shot["segment_id"],
            "shot_index": shot["shot_index"],
            "reason": "prompt_modified",
            "prompt": shot["prompt"],
            "negative_prompt": shot["negative_prompt"],
        })

    # 待重新生成配音的分镜
    audio_shots = db.get_pending_audio_shots(project_id)
    for shot in audio_shots:
        pending_items.append({
            "type": "audio",
            "shot_id": shot["id"],
            "segment_id": shot["segment_id"],
            "shot_index": shot["shot_index"],
            "reason": "audio_params_modified",
            "dialogue": shot["dialogue"],
            "narrator_text": shot["narrator_text"],
            "speaker": shot["speaker"],
        })

    # 待重新合成的段落
    recompose_segs = db.get_pending_recompose_segments(project_id)
    for seg in recompose_segs:
        pending_items.append({
            "type": "compose",
            "segment_id": seg["id"],
            "segment_index": seg["segment_index"],
            "title": seg["title"],
            "reason": seg.get("last_modified_field", "unknown"),
        })

    image_count = sum(1 for i in pending_items if i["type"] == "image")
    audio_count = sum(1 for i in pending_items if i["type"] == "audio")
    compose_count = sum(1 for i in pending_items if i["type"] == "compose")

    return {
        "project_id": project_id,
        "pending_items": pending_items,
        "total_pending": len(pending_items),
        "summary": {
            "image_tasks": image_count,
            "audio_tasks": audio_count,
            "compose_tasks": compose_count,
        },
    }


# ── 批量处理待更新项 ──

@router.post("/{project_id}/process-pending")
def process_pending(project_id: str, body: ProcessPendingRequest):
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "项目不存在")

    results = {
        "image_tasks": [],
        "audio_tasks": [],
        "compose_tasks": [],
    }

    # 收集待处理的图片任务
    if body.scope in ("all",) or body.scope.startswith("segment:"):
        target_seg = body.scope.split(":")[1] if ":" in body.scope else None

        image_shots = db.get_pending_image_shots(project_id)
        for shot in image_shots:
            if target_seg and shot["segment_id"] != target_seg:
                continue
            results["image_tasks"].append({
                "shot_id": shot["id"],
                "segment_id": shot["segment_id"],
                "prompt": shot["prompt"],
                "negative_prompt": shot["negative_prompt"],
            })

        audio_shots = db.get_pending_audio_shots(project_id)
        for shot in audio_shots:
            if target_seg and shot["segment_id"] != target_seg:
                continue
            results["audio_tasks"].append({
                "shot_id": shot["id"],
                "segment_id": shot["segment_id"],
                "dialogue": shot["dialogue"],
                "narrator_text": shot["narrator_text"],
                "speaker": shot["speaker"],
            })

        recompose_segs = db.get_pending_recompose_segments(project_id)
        for seg in recompose_segs:
            if target_seg and seg["id"] != target_seg:
                continue
            results["compose_tasks"].append({
                "segment_id": seg["id"],
                "segment_index": seg["segment_index"],
            })

    total = len(results["image_tasks"]) + len(results["audio_tasks"]) + len(results["compose_tasks"])
    estimated_seconds = len(results["image_tasks"]) * 30 + len(results["audio_tasks"]) * 5 + len(results["compose_tasks"]) * 20

    # 推入 Redis 队列（如果可用）
    from shared.redis_client import queue_push
    for task in results["image_tasks"]:
        queue_push("pending:tasks", {"project_id": project_id, "task_type": "image", **task})
    for task in results["audio_tasks"]:
        queue_push("pending:tasks", {"project_id": project_id, "task_type": "audio", **task})
    for task in results["compose_tasks"]:
        queue_push("pending:tasks", {"project_id": project_id, "task_type": "compose", **task})

    return {
        "project_id": project_id,
        "pending_image_tasks": len(results["image_tasks"]),
        "pending_audio_tasks": len(results["audio_tasks"]),
        "pending_compose_tasks": len(results["compose_tasks"]),
        "total_tasks": total,
        "estimated_time_seconds": estimated_seconds,
        "tasks": results,
        "message": f"已提交 {total} 个任务到处理队列" if total > 0 else "没有待处理的任务",
    }
