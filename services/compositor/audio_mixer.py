import os
import subprocess
import json
from typing import List


def get_audio_duration(audio_path: str) -> float:
    """使用 ffprobe 获取音频时长"""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        audio_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 0.0


def concat_audio(audio_paths: List[str], output_path: str) -> str:
    """拼接多个音频文件"""
    if len(audio_paths) == 1:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_paths[0], "-c", "copy", output_path],
            check=True, capture_output=True,
        )
        return output_path

    # 创建 concat 文件列表
    list_path = output_path + ".list.txt"
    with open(list_path, "w") as f:
        for p in audio_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", output_path],
        check=True, capture_output=True,
    )

    # 清理临时文件
    try:
        os.unlink(list_path)
    except OSError:
        pass

    return output_path


def mix_with_bgm(main_audio: str, bgm_path: str, output_path: str, bgm_volume: float = 0.2) -> str:
    """将主音频与背景音乐混合"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", main_audio,
        "-i", bgm_path,
        "-filter_complex",
        f"[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def adjust_volume(input_path: str, output_path: str, volume: float = 1.0) -> str:
    """调整音频音量"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-af", f"volume={volume}", "-c:a", "aac", output_path],
        check=True, capture_output=True,
    )
    return output_path