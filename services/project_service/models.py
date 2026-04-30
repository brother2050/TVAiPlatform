from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── 项目 ──

class ProjectCreate(BaseModel):
    name: str = "未命名项目"
    author: str = ""
    source_text: str = ""
    split_mode: str = "auto"
    style_hint: str = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    total_segments: Optional[int] = None
    completed_segments: Optional[int] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    author: str
    split_mode: str
    style_hint: str
    status: str
    total_segments: int
    completed_segments: int
    created_at: str
    updated_at: str


# ── 段落 ──

class ShotData(BaseModel):
    shot_index: int
    scene_description: str = ""
    prompt: str = ""
    negative_prompt: str = "blurry, low quality, distorted, deformed"
    dialogue: str = ""
    narrator_text: str = ""
    speaker: str = ""
    camera: str = ""
    characters: List = Field(default_factory=list)
    duration_hint: float = 5.0


class SegmentCreate(BaseModel):
    segment_index: int
    title: str = ""
    content: str = ""
    summary: str = ""
    shots: List[ShotData] = Field(default_factory=list)


class SegmentUpdate(BaseModel):
    status: Optional[str] = None
    video_path: Optional[str] = None
    video_duration: Optional[float] = None
    pending_recompose: Optional[bool] = None
    last_modified_field: Optional[str] = None
    rendered_shots: Optional[int] = None
    failed_shots: Optional[int] = None


class SegmentContentEdit(BaseModel):
    content: str


class SegmentResponse(BaseModel):
    id: str
    project_id: str
    segment_index: int
    title: str
    content: str
    summary: str
    status: str
    total_shots: int
    rendered_shots: int
    failed_shots: int
    pending_recompose: bool
    video_path: str
    video_duration: float
    created_at: str
    updated_at: str


# ── 分镜 ──

class ShotImageUpdate(BaseModel):
    image_path: str
    prompt: Optional[str] = None
    version: Optional[int] = None


class ShotAudioUpdate(BaseModel):
    audio_path: str
    duration: float = 0


class ShotRegenerate(BaseModel):
    action: str = "regenerate"
    new_prompt: Optional[str] = None
    new_negative_prompt: Optional[str] = None
    new_description: Optional[str] = None


class ShotScriptEdit(BaseModel):
    scene_description: Optional[str] = None
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    dialogue: Optional[str] = None
    narrator_text: Optional[str] = None
    speaker: Optional[str] = None
    camera: Optional[str] = None


class ShotAudioParamsEdit(BaseModel):
    text: Optional[str] = None
    speaker: Optional[str] = None
    speed: Optional[float] = None


class ShotResponse(BaseModel):
    id: str
    segment_id: str
    shot_index: int
    scene_description: str
    prompt: str
    negative_prompt: str
    dialogue: str
    narrator_text: str
    speaker: str
    camera: str
    characters_json: str
    duration_hint: float
    image_path: str
    audio_path: str
    audio_duration: float
    status: str
    current_version: int
    is_current: bool
    image_source: str
    audio_source: str
    pending_image_regen: bool
    pending_audio_regen: bool
    created_at: str
    updated_at: str


class ShotVersionResponse(BaseModel):
    id: str
    shot_id: str
    version: int
    image_path: str
    prompt: str
    negative_prompt: str
    source: str
    created_at: str


# ── 合成参数 ──

class SubtitleParams(BaseModel):
    enabled: bool = True
    font_size: int = 24
    font_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    position: str = "bottom_center"


class TransitionParams(BaseModel):
    type: str = "fade"
    duration: float = 0.5


class TitleParams(BaseModel):
    enabled: bool = True
    text: str = ""
    duration: float = 3.0


class BgmParams(BaseModel):
    enabled: bool = False
    file_path: str = ""
    volume: float = 0.2


class RecomposeParams(BaseModel):
    subtitle: Optional[SubtitleParams] = None
    transition: Optional[TransitionParams] = None
    title: Optional[TitleParams] = None
    background_music: Optional[BgmParams] = None
    output_format: str = "horizontal_16_9"


# ── 批量处理 ──

class ProcessPendingRequest(BaseModel):
    scope: str = "all"