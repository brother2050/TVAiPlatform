"""ChatTTS 核心功能模块"""

import os
import io
import base64
import numpy as np
import ChatTTS
import torch
from typing import Optional, List, Dict, Any
from pathlib import Path


class ChatTTSEngine:
    """ChatTTS 引擎封装类"""

    _instance: Optional["ChatTTSEngine"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.chat = None
        self._initialized = True

    def initialize(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """初始化 ChatTTS 模型"""
        if self.chat is not None:
            return

        self.chat = ChatTTS.Chat()
        
        # 加载模型
        if device == "cuda" and torch.cuda.is_available():
            self.chat.load(source="huggingface", device=device)
        else:
            self.chat.load(source="huggingface")

        self.device = device
        print(f"[ChatTTS] 模型加载完成，设备: {self.device}")

    def synthesize(
        self,
        text: str,
        voice_seed: Optional[int] = None,
        voice_params: Optional[Dict[str, Any]] = None,
        infer_params: Optional[Dict[str, Any]] = None,
        refine_params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> np.ndarray:
        """
        合成语音
        
        Args:
            text: 输入文本
            voice_seed: 音色随机种子
            voice_params: 音色参数
            infer_params: 推理参数 (temperature, top_P, top_K)
            refine_params: 文本优化参数 (prompt)
            stream: 是否使用流式推理
            
        Returns:
            音频数据 (numpy array)
        """
        if self.chat is None:
            raise RuntimeError("ChatTTS 引擎未初始化")

        # 配置推理参数 (InferCodeParams)
        if infer_params is None:
            infer_params = {}
        
        params_infer = self.chat.InferCodeParams(
            temperature=infer_params.get("temperature", 0.3),
            top_P=infer_params.get("top_P", 0.7),
            top_K=infer_params.get("top_K", 20),
            repetition_penalty=infer_params.get("repetition_penalty", 1.05),
        )

        # 配置文本优化参数 (RefineTextParams)
        if refine_params is None:
            refine_params = {}
        
        params_refine = self.chat.RefineTextParams(
            prompt=refine_params.get("prompt", ""),
        )

        # 配置音色 - 通过 manual_seed
        if voice_seed is not None:
            params_infer.manual_seed = voice_seed
        elif voice_params is not None and voice_params.get("seed"):
            params_infer.manual_seed = voice_params.get("seed")

        # 执行推理
        if stream:
            # 流式推理模式
            wav_stream = self.chat.infer(
                text,
                stream=True,
                params_refine_text=params_refine,
                params_infer_code=params_infer,
            )
            # 合并流式音频
            audio_chunks = []
            for chunk in wav_stream:
                if isinstance(chunk, np.ndarray):
                    audio_chunks.append(chunk)
            return np.concatenate(audio_chunks) if audio_chunks else np.array([])
        else:
            # 普通推理模式
            wav = self.chat.infer(
                text,
                stream=False,
                params_refine_text=params_refine,
                params_infer_code=params_infer,
            )
            return wav[0] if isinstance(wav, (list, tuple)) and len(wav) > 0 else np.array([])

    def synthesize_to_bytes(
        self,
        text: str,
        voice_seed: Optional[int] = None,
        voice_params: Optional[Dict[str, Any]] = None,
        infer_params: Optional[Dict[str, Any]] = None,
        refine_params: Optional[Dict[str, Any]] = None,
        sample_rate: int = 24000,
    ) -> bytes:
        """
        合成语音并返回 WAV 字节数据
        
        Returns:
            WAV 格式的字节数据
        """
        audio = self.synthesize(
            text=text,
            voice_seed=voice_seed,
            voice_params=voice_params,
            infer_params=infer_params,
            refine_params=refine_params,
        )
        
        return self._audio_to_wav(audio, sample_rate)

    def _audio_to_wav(self, audio: np.ndarray, sample_rate: int = 24000) -> bytes:
        """将音频数组转换为 WAV 字节"""
        import wave

        # 归一化到 [-1, 1]
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        if audio.size > 0:
            max_val = max(abs(audio.max()), abs(audio.min()))
            if max_val > 1.0:
                audio = audio / max_val

        # 转换为 16-bit PCM
        audio_pcm = (audio * 32767).astype(np.int16)

        # 创建 WAV 字节
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_pcm.tobytes())

        return buffer.getvalue()

    def audio_to_base64(self, audio_bytes: bytes) -> str:
        """将音频字节转换为 Base64 字符串"""
        return base64.b64encode(audio_bytes).decode("utf-8")


# 全局引擎实例
_engine: Optional[ChatTTSEngine] = None


def get_engine() -> ChatTTSEngine:
    """获取 ChatTTS 引擎单例"""
    global _engine
    if _engine is None:
        _engine = ChatTTSEngine()
    return _engine


def init_engine(device: str = None) -> ChatTTSEngine:
    """初始化 ChatTTS 引擎"""
    engine = get_engine()
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    engine.initialize(device)
    return engine
