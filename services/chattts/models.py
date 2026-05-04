"""ChatTTS 数据模型定义"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from enum import Enum


class GenderType(str, Enum):
    """音色性别类型"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class AgeType(str, Enum):
    """音色年龄类型"""
    YOUNG = "young"
    MIDDLE = "middle"
    OLD = "old"


class ReturnFormat(str, Enum):
    """返回格式"""
    FILE = "file"       # 返回文件路径
    BASE64 = "base64"   # 返回 Base64 流
    WAV_BYTES = "bytes" # 返回 WAV 原始字节


class InferCodeParams(BaseModel):
    """推理参数配置"""
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="采样温度，控制随机性"
    )
    top_P: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="核采样阈值"
    )
    top_K: int = Field(
        default=20,
        ge=1,
        le=100,
        description="采样时考虑的 top-K token 数量"
    )
    repetition_penalty: float = Field(
        default=1.05,
        ge=1.0,
        le=2.0,
        description="重复惩罚"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 0.3,
                "top_P": 0.7,
                "top_K": 20,
                "repetition_penalty": 1.05
            }
        }


class RefineTextParams(BaseModel):
    """文本优化参数配置"""
    prompt: str = Field(
        default="",
        description="文本优化提示词"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": ""
            }
        }


class VoiceParams(BaseModel):
    """音色参数配置"""
    gender: GenderType = Field(
        default=GenderType.FEMALE,
        description="音色性别"
    )
    age: AgeType = Field(
        default=AgeType.MIDDLE,
        description="音色年龄"
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="语速倍数"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "gender": "female",
                "age": "middle",
                "speed": 1.0
            }
        }


class SynthesizeRequest(BaseModel):
    """语音合成请求"""
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="要合成的文本内容"
    )
    voice_seed: Optional[int] = Field(
        default=None,
        description="音色随机种子，用于生成确定性音色"
    )
    voice_params: Optional[VoiceParams] = Field(
        default=None,
        description="自定义音色参数"
    )
    infer_params: Optional[InferCodeParams] = Field(
        default=None,
        description="推理参数"
    )
    refine_params: Optional[RefineTextParams] = Field(
        default=None,
        description="文本优化参数"
    )
    return_format: ReturnFormat = Field(
        default=ReturnFormat.FILE,
        description="返回格式：file(文件路径)、base64(Base64流)、bytes(WAV字节)"
    )
    output_filename: Optional[str] = Field(
        default=None,
        description="输出文件名（不含扩展名）"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """验证并清理文本"""
        v = v.replace("\x00", "")
        v = " ".join(v.split())
        if not v.strip():
            raise ValueError("文本不能为空")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "text": "你好，这是一个测试音频。",
                "voice_seed": 42,
                "infer_params": {
                    "temperature": 0.3,
                    "top_P": 0.7,
                    "top_K": 20
                },
                "refine_params": {
                    "prompt": ""
                },
                "return_format": "base64"
            }
        }


class BatchSynthesizeRequest(BaseModel):
    """批量语音合成请求"""
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="要合成的文本列表"
    )
    voice_seed: Optional[int] = Field(
        default=None,
        description="统一音色随机种子"
    )
    voice_params: Optional[VoiceParams] = Field(
        default=None,
        description="统一音色参数"
    )
    infer_params: Optional[InferCodeParams] = Field(
        default=None,
        description="统一推理参数"
    )
    refine_params: Optional[RefineTextParams] = Field(
        default=None,
        description="统一文本优化参数"
    )
    return_format: ReturnFormat = Field(
        default=ReturnFormat.BASE64,
        description="返回格式"
    )


class PresetVoice(BaseModel):
    """预存音色定义"""
    id: str = Field(..., description="音色ID")
    name: str = Field(..., description="音色名称")
    description: str = Field(default="", description="音色描述")
    seed: int = Field(..., description="对应的随机种子")
    infer_params: Optional[InferCodeParams] = Field(
        default=None,
        description="推荐推理参数"
    )
    refine_params: Optional[RefineTextParams] = Field(
        default=None,
        description="推荐文本优化参数"
    )
    category: str = Field(default="custom", description="音色分类")
    is_default: bool = Field(default=False, description="是否为默认音色")


class PresetVoiceCreate(BaseModel):
    """创建预存音色请求"""
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)
    seed: int = Field(..., description="随机种子")
    infer_params: Optional[InferCodeParams] = None
    refine_params: Optional[RefineTextParams] = None
    category: str = Field(default="custom", max_length=50)


class SynthesizeResponse(BaseModel):
    """语音合成响应"""
    success: bool = Field(..., description="是否成功")
    audio_path: Optional[str] = Field(default=None, description="音频文件路径")
    audio_base64: Optional[str] = Field(default=None, description="Base64 音频流")
    duration: float = Field(default=0.0, description="音频时长（秒）")
    sample_rate: int = Field(default=24000, description="采样率")
    message: str = Field(default="", description="消息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class BatchSynthesizeResponse(BaseModel):
    """批量语音合成响应"""
    success: bool
    total: int
    succeeded: int
    failed: int
    results: List[SynthesizeResponse]
    combined_path: Optional[str] = None
    combined_base64: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    device: str
    model_loaded: bool
