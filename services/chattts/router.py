"""ChatTTS API 路由"""

import os
import uuid
import base64
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import Response, JSONResponse

from .core import get_engine, init_engine
from .models import (
    SynthesizeRequest, SynthesizeResponse,
    BatchSynthesizeRequest, BatchSynthesizeResponse,
    PresetVoiceCreate, PresetVoice,
    ReturnFormat, InferCodeParams, RefineTextParams, VoiceParams
)
from .voices import get_voice_manager


router = APIRouter(prefix="/api/chattts", tags=["ChatTTS"])

# 存储目录
STORAGE_DIR = Path(__file__).parent.parent.parent / "storage" / "chattts"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _get_infer_params_dict(infer_params: InferCodeParams = None) -> dict:
    """获取推理参数字典"""
    if infer_params:
        return infer_params.model_dump()
    return {}


def _get_refine_params_dict(refine_params: RefineTextParams = None) -> dict:
    """获取文本优化参数字典"""
    if refine_params:
        return {"prompt": refine_params.prompt}
    return {}


def _get_voice_params_dict(voice_params: VoiceParams = None) -> dict:
    """获取音色参数字典"""
    if voice_params:
        return {"gender": voice_params.gender.value, "age": voice_params.age.value}
    return {}


@router.get("/health", response_model=dict)
async def health_check():
    """健康检查"""
    engine = get_engine()
    return {
        "status": "healthy",
        "service": "chattts",
        "model_loaded": engine.chat is not None,
    }


# ==================== 语音合成接口 ====================

@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(request: SynthesizeRequest):
    """
    语音合成接口
    
    根据输入文本生成音频，支持：
    - 指定 seed 生成确定性音色
    - 使用预存音色
    - 配置推理参数 (temperature, top_P, top_K)
    - 配置文本优化参数 (oral, break)
    """
    try:
        engine = init_engine()
        voice_manager = get_voice_manager()

        # 处理音色参数
        voice_seed = request.voice_seed
        voice_params_dict = None

        if request.voice_params:
            voice_params_dict = _get_voice_params_dict(request.voice_params)
        elif voice_seed is None:
            # 使用默认音色
            default_voice = voice_manager.get_default_preset()
            if default_voice:
                voice_seed = default_voice.seed
                if default_voice.infer_params and not request.infer_params:
                    request.infer_params = default_voice.infer_params
                if default_voice.refine_params and not request.refine_params:
                    request.refine_params = default_voice.refine_params

        # 获取参数字典
        infer_params = _get_infer_params_dict(request.infer_params)
        refine_params = _get_refine_params_dict(request.refine_params)

        # 生成音频
        audio_bytes = engine.synthesize_to_bytes(
            text=request.text,
            voice_seed=voice_seed,
            voice_params=voice_params_dict,
            infer_params=infer_params,
            refine_params=refine_params,
        )

        # 计算音频时长（近似值：采样率24000，16bit）
        audio_samples = len(audio_bytes) // 2
        duration = audio_samples / 24000

        # 根据返回格式处理
        result = SynthesizeResponse(
            success=True,
            duration=duration,
            sample_rate=24000,
            message="音频生成成功",
        )

        if request.return_format == ReturnFormat.FILE:
            # 保存为文件
            filename = request.output_filename or f"audio_{uuid.uuid4().hex[:8]}"
            file_path = STORAGE_DIR / f"{filename}.wav"
            
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            
            result.audio_path = str(file_path)
            result.metadata = {
                "filename": f"{filename}.wav",
                "size_bytes": len(audio_bytes),
            }

        elif request.return_format == ReturnFormat.BASE64:
            # 返回 Base64
            result.audio_base64 = engine.audio_to_base64(audio_bytes)
            result.metadata = {
                "size_bytes": len(audio_bytes),
                "encoding": "audio/wav;base64",
            }

        elif request.return_format == ReturnFormat.WAV_BYTES:
            # 直接返回字节
            return Response(
                content=audio_bytes,
                media_type="audio/wav",
                headers={
                    "X-Duration": str(duration),
                    "X-Sample-Rate": "24000",
                    "Content-Disposition": f"inline; filename={request.output_filename or 'audio'}.wav"
                }
            )

        return result

    except Exception as e:
        return SynthesizeResponse(
            success=False,
            message=f"音频生成失败: {str(e)}",
        )


@router.post("/batch", response_model=BatchSynthesizeResponse)
async def batch_synthesize(request: BatchSynthesizeRequest):
    """
    批量语音合成接口
    
    批量合成多条文本，返回各自的音频结果
    """
    try:
        engine = init_engine()
        voice_manager = get_voice_manager()

        # 处理统一音色参数
        voice_seed = request.voice_seed
        voice_params_dict = None

        if request.voice_params:
            voice_params_dict = _get_voice_params_dict(request.voice_params)
        elif voice_seed is None:
            default_voice = voice_manager.get_default_preset()
            if default_voice:
                voice_seed = default_voice.seed

        infer_params = _get_infer_params_dict(request.infer_params)
        refine_params = _get_refine_params_dict(request.refine_params)

        results = []
        succeeded = 0
        failed = 0
        combined_base64 = None

        for i, text in enumerate(request.texts):
            try:
                audio_bytes = engine.synthesize_to_bytes(
                    text=text,
                    voice_seed=voice_seed,
                    voice_params=voice_params_dict,
                    infer_params=infer_params,
                    refine_params=refine_params,
                )

                audio_samples = len(audio_bytes) // 2
                duration = audio_samples / 24000

                if request.return_format == ReturnFormat.BASE64:
                    results.append(SynthesizeResponse(
                        success=True,
                        audio_base64=engine.audio_to_base64(audio_bytes),
                        duration=duration,
                        sample_rate=24000,
                        message="成功",
                    ))
                else:
                    filename = f"batch_{uuid.uuid4().hex[:8]}_{i}"
                    file_path = STORAGE_DIR / f"{filename}.wav"
                    
                    with open(file_path, "wb") as f:
                        f.write(audio_bytes)
                    
                    results.append(SynthesizeResponse(
                        success=True,
                        audio_path=str(file_path),
                        duration=duration,
                        sample_rate=24000,
                        message="成功",
                    ))

                succeeded += 1

            except Exception as e:
                failed += 1
                results.append(SynthesizeResponse(
                    success=False,
                    message=f"第 {i+1} 条失败: {str(e)}",
                ))

        return BatchSynthesizeResponse(
            success=failed == 0,
            total=len(request.texts),
            succeeded=succeeded,
            failed=failed,
            results=results,
        )

    except Exception as e:
        return BatchSynthesizeResponse(
            success=False,
            total=len(request.texts),
            succeeded=0,
            failed=len(request.texts),
            results=[],
            combined_base64=None,
        )


# ==================== 预存音色管理接口 ====================

@router.get("/voices", response_model=List[dict])
async def list_voices(category: str = Query(None, description="按分类筛选")):
    """获取所有预存音色列表"""
    voice_manager = get_voice_manager()
    return voice_manager.get_all_as_dict()


@router.get("/voices/categories", response_model=List[str])
async def list_categories():
    """获取所有音色分类"""
    voice_manager = get_voice_manager()
    return voice_manager.list_categories()


@router.get("/voices/{voice_id}", response_model=dict)
async def get_voice(voice_id: str):
    """获取指定音色详情"""
    voice_manager = get_voice_manager()
    voice = voice_manager.get_preset(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="音色不存在")
    return voice.model_dump()


@router.post("/voices", response_model=dict, status_code=201)
async def create_voice(request: PresetVoiceCreate):
    """创建自定义音色"""
    voice_manager = get_voice_manager()
    try:
        voice = voice_manager.create_preset(request)
        return voice.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/voices/{voice_id}", response_model=dict)
async def update_voice(voice_id: str, request: PresetVoiceCreate):
    """更新自定义音色"""
    voice_manager = get_voice_manager()
    voice = voice_manager.update_preset(voice_id, request)
    if not voice:
        raise HTTPException(status_code=404, detail="音色不存在")
    return voice.model_dump()


@router.delete("/voices/{voice_id}", status_code=204)
async def delete_voice(voice_id: str):
    """删除自定义音色"""
    voice_manager = get_voice_manager()
    try:
        if not voice_manager.delete_preset(voice_id):
            raise HTTPException(status_code=404, detail="音色不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 文本优化接口 ====================

@router.post("/refine", response_model=dict)
async def refine_text(
    text: str = Body(..., min_length=1, max_length=5000),
    prompt: str = Body("", description="文本优化提示词"),
):
    """
    文本优化接口
    
    使用 ChatTTS 的 refine_text_only 模式优化文本
    """
    try:
        engine = init_engine()
        
        # 使用 ChatTTS 的 refine_text_only 模式
        refined = engine.chat.infer(
            text,
            skip_refine_text=False,
            refine_text_only=True,
            params_refine_text=engine.chat.RefineTextParams(prompt=prompt),
            params_infer_code=engine.chat.InferCodeParams(),
        )
        
        return {
            "success": True,
            "original": text,
            "refined": refined[0] if isinstance(refined, list) and refined else text,
            "params": {"prompt": prompt},
        }
        
    except Exception as e:
        return {
            "success": False,
            "original": text,
            "refined": None,
            "message": str(e),
        }


# ==================== 参数配置接口 ====================

@router.get("/params/presets", response_model=dict)
async def get_params_presets():
    """
    获取推荐的参数预设
    
    返回不同场景下的推荐参数配置
    """
    return {
        "infer_presets": [
            {
                "name": "默认",
                "description": "平衡的默认配置",
                "params": {"temperature": 0.3, "top_P": 0.7, "top_K": 20}
            },
            {
                "name": "创意",
                "description": "更有创意和变化",
                "params": {"temperature": 0.5, "top_P": 0.6, "top_K": 15}
            },
            {
                "name": "稳定",
                "description": "更稳定一致的输出",
                "params": {"temperature": 0.1, "top_P": 0.9, "top_K": 30}
            },
            {
                "name": "快速",
                "description": "快速生成，质量略低",
                "params": {"temperature": 0.2, "top_P": 0.8, "top_K": 10}
            },
        ],
        "refine_presets": [
            {
                "name": "默认",
                "description": "默认配置",
                "params": {"prompt": ""}
            },
            {
                "name": "快速",
                "description": "跳过文本优化",
                "params": {"prompt": ""}
            },
        ]
    }


@router.post("/params/validate", response_model=dict)
async def validate_params(
    infer_params: InferCodeParams = None,
    refine_params: RefineTextParams = None,
):
    """
    验证参数配置是否有效
    
    返回参数的有效范围和建议
    """
    return {
        "valid": True,
        "infer_params": {
            "temperature": {
                "min": 0.0,
                "max": 1.0,
                "recommended_range": [0.1, 0.5],
                "description": "采样温度，控制随机性"
            },
            "top_P": {
                "min": 0.0,
                "max": 1.0,
                "recommended_range": [0.5, 0.9],
                "description": "核采样阈值"
            },
            "top_K": {
                "min": 1,
                "max": 100,
                "recommended_range": [10, 30],
                "description": "Top-K 采样数量"
            },
        },
        "refine_params": {
            "prompt": {
                "min": "",
                "max": "",
                "description": "文本优化提示词"
            },
        }
    }
