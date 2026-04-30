import os
from typing import List, Dict, Any, Optional


def _hex_to_ass_color(hex_color: str) -> str:
    """将 #RRGGBB 转换为 ASS 颜色格式 &HBBGGRR&"""
    hex_color = hex_color.lstrip("#")
    r = hex_color[0:2]
    g = hex_color[2:4]
    b = hex_color[4:6]
    return f"&H00{b}{g}{r}&"


def generate_srt(shots: List[Dict[str, Any]], output_path: str) -> str:
    """根据分镜数据生成 SRT 字幕文件"""
    lines = []
    index = 1
    current_time = 0.0

    for shot in shots:
        duration = shot.get("audio_duration", 5.0)
        if duration <= 0:
            duration = 5.0

        text = shot.get("dialogue", "") or shot.get("narrator_text", "")
        if not text.strip():
            current_time += duration
            continue

        start = current_time
        end = current_time + duration

        start_ts = _seconds_to_srt_time(start)
        end_ts = _seconds_to_srt_time(end)

        lines.append(f"{index}")
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text.strip())
        lines.append("")

        index += 1
        current_time = end

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def generate_ass(shots: List[Dict[str, Any]], output_path: str, config: Optional[Dict[str, Any]] = None) -> str:
    """根据分镜数据生成 ASS 字幕文件（支持更丰富的样式）"""
    if config is None:
        config = {}

    font_size = config.get("font_size", 24)
    primary_color = _hex_to_ass_color(config.get("font_color", "#FFFFFF"))
    outline_color = _hex_to_ass_color(config.get("outline_color", "#000000"))
    position = config.get("position", "bottom_center")

    # 根据位置设置对齐值（ASS 对齐：2=底部居中，8=顶部居中，5=中央）
    alignment = 2
    margin_v = 30
    if position == "top_center":
        alignment = 8
        margin_v = 30
    elif position == "center":
        alignment = 5
        margin_v = 0

    header = f"""[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,{font_size},{primary_color},&H000000&,{outline_color},&H80000000&,0,0,0,0,100,100,0,0,1,2,1,{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    current_time = 0.0

    for shot in shots:
        duration = shot.get("audio_duration", 5.0)
        if duration <= 0:
            duration = 5.0

        text = shot.get("dialogue", "") or shot.get("narrator_text", "")
        if not text.strip():
            current_time += duration
            continue

        start_ts = _seconds_to_ass_time(current_time)
        end_ts = _seconds_to_ass_time(current_time + duration)

        # 转义 ASS 特殊字符
        text = text.strip().replace("\n", "\\N")

        events.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{text}")
        current_time += duration

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(events))
        f.write("\n")

    return output_path


def _seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _seconds_to_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"