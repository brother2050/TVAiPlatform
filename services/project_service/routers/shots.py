import os
import json
import shutil
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File
from services.project_service.models import (
    ShotImageUpdate, ShotAudioUpdate, ShotRegenerate,
    ShotScriptEdit, ShotAudioParamsEdit,
)
from services.project_service import db
from shared.storage import get_storage

router = APIRouter(prefix="/api/shots", tags=["shots"])


# ── 查询分镜详情 ──

@router.get("/{shot_id}")
def get_shot(shot_id: str):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")
    return _to_dict(shot)


# ── 更新分镜图片 ──

@router.post("/{shot_id}/image")
def update_shot_image(shot_id: str, body: ShotImageUpdate):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")

    new_version = body.version or (shot["current_version"] + 1)
    prompt = body.prompt if body.prompt is not None else shot["prompt"]

    # 记录版本
    db.create_shot_version(
        shot_id=shot_id,
        version=new_version,
        image_path=body.image_path,
        prompt=prompt,
        negative_prompt=shot["negative_prompt"],
        source="edited" if body.prompt else "generated",
    )

    # 更新分镜
    updates = {
        "image_path": body.image_path,
        "current_version": new_version,
        "image_source": "generated",
        "pending_image_regen": 0,
        "status": "image_done" if not shot["audio_path"] else "completed",
    }
    if body.prompt is not None:
        updates["prompt"] = body.prompt

    db.update_shot(shot_id, **updates)

    # 更新段落渲染计数
    _update_segment_render_counts(shot["segment_id"])

    return {
        "shot_id": shot_id,
        "status": "updated",
        "image_path": body.image_path,
        "version": new_version,
    }


# ── 更新分镜音频 ──

@router.post("/{shot_id}/audio")
def update_shot_audio(shot_id: str, body: ShotAudioUpdate):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")

    updates = {
        "audio_path": body.audio_path,
        "audio_duration": body.duration,
        "audio_source": "generated",
        "pending_audio_regen": 0,
    }

    # 如果图片也有了，标记为 completed
    if shot["image_path"]:
        updates["status"] = "completed"
    else:
        updates["status"] = "audio_done"

    db.update_shot(shot_id, **updates)
    _update_segment_render_counts(shot["segment_id"])

    return {
        "shot_id": shot_id,
        "status": "updated",
        "audio_path": body.audio_path,
        "duration": body.duration,
    }


# ── 重新生成分镜图片 ──

@router.post("/{shot_id}/regenerate")
def regenerate_shot(shot_id: str, body: ShotRegenerate):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")

    new_version = shot["current_version"] + 1

    if body.action == "regenerate":
        # 标记待重新生成，返回当前 prompt 供 Dify 使用
        db.update_shot(shot_id, pending_image_regen=1, status="pending")
        return {
            "shot_id": shot_id,
            "action": "regenerate",
            "prompt": shot["prompt"],
            "negative_prompt": shot["negative_prompt"],
            "version": new_version,
            "message": "已标记为待重新生成，请使用当前提示词调用生图引擎",
        }

    elif body.action == "edit_and_regenerate":
        updates = {"pending_image_regen": 1, "status": "pending"}
        if body.new_prompt:
            updates["prompt"] = body.new_prompt
        if body.new_negative_prompt:
            updates["negative_prompt"] = body.new_negative_prompt
        if body.new_description:
            updates["scene_description"] = body.new_description
        db.update_shot(shot_id, **updates)

        return {
            "shot_id": shot_id,
            "action": "edit_and_regenerate",
            "prompt": body.new_prompt or shot["prompt"],
            "negative_prompt": body.new_negative_prompt or shot["negative_prompt"],
            "scene_description": body.new_description or shot["scene_description"],
            "version": new_version,
            "message": "已更新提示词并标记为待重新生成",
        }

    else:
        raise HTTPException(400, f"不支持的操作: {body.action}")


# ── 编辑分镜脚本 ──

@router.put("/{shot_id}/script")
def edit_shot_script(shot_id: str, body: ShotScriptEdit):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")

    updates = {}
    changed_fields = []
    need_image = False
    need_audio = False

    image_fields = {"scene_description", "prompt", "negative_prompt"}
    audio_fields = {"dialogue", "narrator_text", "speaker"}

    for field, value in body.model_dump(exclude_none=True).items():
        if value != shot.get(field, ""):
            updates[field] = value
            changed_fields.append(field)
            if field in image_fields:
                need_image = True
            if field in audio_fields:
                need_audio = True

    if not updates:
        return {"shot_id": shot_id, "changed_fields": [], "message": "无变更"}

    if need_image:
        updates["pending_image_regen"] = 1
    if need_audio:
        updates["pending_audio_regen"] = 1

    db.update_shot(shot_id, **updates)

    # 标记段落待重新合成
    segment = db.get_segment(shot["segment_id"])
    if segment and not segment["pending_recompose"]:
        db.update_segment(shot["segment_id"], pending_recompose=1, last_modified_field="shots")

    action_parts = []
    if need_image:
        action_parts.append("图片")
    if need_audio:
        action_parts.append("配音")

    return {
        "shot_id": shot_id,
        "changed_fields": changed_fields,
        "need_regenerate_image": need_image,
        "need_regenerate_audio": need_audio,
        "action_required": f"regenerate_{'_and_'.join(action_parts)}" if action_parts else "none",
        "message": f"{'和'.join(changed_fields)}已修改" + (f"，需要重新生成{'和'.join(action_parts)}" if action_parts else ""),
    }


# ── 编辑配音参数 ──

@router.put("/{shot_id}/audio_params")
def edit_audio_params(shot_id: str, body: ShotAudioParamsEdit):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")

    updates = {}
    if body.text is not None:
        updates["dialogue"] = body.text
    if body.speaker is not None:
        updates["speaker"] = body.speaker

    if updates:
        updates["pending_audio_regen"] = 1
        db.update_shot(shot_id, **updates)

    return {
        "shot_id": shot_id,
        "need_regenerate_audio": bool(updates),
        "message": "配音参数已修改，需要重新生成配音" if updates else "无变更",
    }


# ── 上传替换图片 ──

@router.post("/{shot_id}/image/upload")
async def upload_shot_image(shot_id: str, image_file: UploadFile = File(...)):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")

    segment = db.get_segment(shot["segment_id"])
    if not segment:
        raise HTTPException(404, "段落不存在")

    storage = get_storage()
    ext = os.path.splitext(image_file.filename or "")[1] or ".png"  # type: ignore[arg-type]
    new_version = shot["current_version"] + 1
    relative_path = f"projects/{segment['project_id']}/segments/{shot['segment_id']}/shots/{shot_id}/v{new_version}{ext}"

    content = await image_file.read()
    file_path = storage.save_bytes(relative_path, content)

    # 记录版本
    db.create_shot_version(
        shot_id=shot_id, version=new_version, image_path=file_path,
        prompt=shot["prompt"], negative_prompt=shot["negative_prompt"], source="uploaded",
    )

    db.update_shot(
        shot_id,
        image_path=file_path,
        current_version=new_version,
        image_source="uploaded",
        pending_image_regen=0,
        status="completed" if shot["audio_path"] else "image_done",
    )

    _update_segment_render_counts(shot["segment_id"])

    return {
        "shot_id": shot_id,
        "image_path": file_path,
        "source": "uploaded",
        "version": new_version,
    }


# ── 上传替换音频 ──

@router.post("/{shot_id}/audio/upload")
async def upload_shot_audio(shot_id: str, audio_file: UploadFile = File(...)):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")

    segment = db.get_segment(shot["segment_id"])
    if not segment:
        raise HTTPException(404, "段落不存在")

    storage = get_storage()
    ext = os.path.splitext(audio_file.filename or "")[1] or ".wav"  # type: ignore[arg-type]
    relative_path = f"projects/{segment['project_id']}/segments/{shot['segment_id']}/shots/{shot_id}/custom{ext}"

    content = await audio_file.read()
    file_path = storage.save_bytes(relative_path, content)

    db.update_shot(
        shot_id,
        audio_path=file_path,
        audio_source="uploaded",
        pending_audio_regen=0,
        status="completed" if shot["image_path"] else "audio_done",
    )

    _update_segment_render_counts(shot["segment_id"])

    return {
        "shot_id": shot_id,
        "audio_path": file_path,
        "source": "uploaded",
    }


# ── 查询分镜历史版本 ──

@router.get("/{shot_id}/versions")
def get_shot_versions(shot_id: str):
    shot = db.get_shot(shot_id)
    if not shot:
        raise HTTPException(404, "分镜不存在")

    versions = db.get_shot_versions(shot_id)
    return {
        "shot_id": shot_id,
        "current_version": shot["current_version"],
        "versions": [dict(v) for v in versions],
    }


# ── 辅助函数 ──

def _update_segment_render_counts(segment_id: str):
    counts = db.count_shots_by_status(segment_id)
    rendered = counts.get("completed", 0) + counts.get("confirmed", 0)
    failed = counts.get("failed", 0)
    db.update_segment(segment_id, rendered_shots=rendered, failed_shots=failed)


def _to_dict(s: dict) -> dict:
    result = dict(s)
    result["is_current"] = bool(result.get("is_current", 1))
    result["pending_image_regen"] = bool(result.get("pending_image_regen", 0))
    result["pending_audio_regen"] = bool(result.get("pending_audio_regen", 0))
    return result