import os
import subprocess
import tempfile


def generate_title_video(
    text: str,
    duration: float,
    output_path: str,
    resolution: str = "1920x1080",
    fps: int = 30,
    bg_color: str = "#1a1a1a",
    text_color: str = "#ffffff",
) -> str:
    """使用 FFmpeg 生成片头视频（纯色背景 + 居中文字）"""
    w, h = resolution.split("x")

    # 使用 FFmpeg 的 drawtext 滤镜
    # 注意：需要系统安装支持中文的字体
    escaped_text = text.replace("'", "'\\''").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={resolution}:r={fps}:d={duration}",
        "-vf", (
            f"drawtext=text='{escaped_text}'"
            f":fontcolor={text_color}"
            f":fontsize=64"
            f":x=(w-text_w)/2"
            f":y=(h-text_h)/2"
            f":fontfile=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        ),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        output_path,
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        # 如果没有中文字体，尝试不指定字体
        cmd_no_font = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={resolution}:r={fps}:d={duration}",
            "-vf", f"drawtext=text='{escaped_text}':fontcolor={text_color}:fontsize=64:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            output_path,
        ]
        subprocess.run(cmd_no_font, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        # 如果 drawtext 失败，生成纯色片头
        cmd_plain = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={resolution}:r={fps}:d={duration}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            output_path,
        ]
        subprocess.run(cmd_plain, check=True, capture_output=True, text=True)

    return output_path
