from pydantic import BaseModel, Field
from typing import Optional, List


class ShotInput(BaseModel):
    shot_id: str
    shot_index: int
    image_path: str
    audio_path: str = ""
    audio_duration: float = 5.0
    dialogue: str = ""
    narrator_text: str = ""
    speaker: str = ""
    camera: str = ""


class SubtitleConfig(BaseModel):
    enabled: bool = True
    font_size: int = 24
    font_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    position: str = "bottom_center"


class TransitionConfig(BaseModel):
    type: str = "fade"
    duration: float = 0.5


class TitleConfig(BaseModel):
    enabled: bool = True
    text: str = ""
    duration: float = 3.0


class BgmConfig(BaseModel):
    enabled: bool = False
    file_path: str = ""
    volume: float = 0.2


class ComposeRequest(BaseModel):
    segment_id: str
    shots: List[ShotInput]
    output_format: str = "horizontal_16_9"
    subtitle: SubtitleConfig = Field(default_factory=SubtitleConfig)
    transition: TransitionConfig = Field(default_factory=TransitionConfig)
    title: TitleConfig = Field(default_factory=TitleConfig)
    background_music: Optional[BgmConfig] = None


class ComposeStatus(BaseModel):
    task_id: str
    status: str
    progress_percent: int = 0
    current_step: str = ""
    estimated_remaining_seconds: int = 0
    video_path: str = ""
    duration: float = 0
    resolution: str = ""
    file_size_mb: float = 0