import os
import subprocess
import json
import shutil
import tempfile
from typing import List, Tuple, Optional, Callable, Dict, Any
from PIL import Image

from services.compositor.subtitle import generate_srt, generate_ass
from services.compositor.title_card import generate_title_video
from services.compositor.audio_mixer import get_audio_duration, concat_audio, mix_with_bgm


RESOLUTIONS = {
    "horizontal_16_9": (1920, 1080),
    "vertical_9_16": (1080, 1920),
    "square_1_1": (1080, 1080),
}


def get_resolution(output_format: str) -> Tuple[int, int]:
    return RESOLUTIONS.get(output_format, (1920, 1080))


def compose_segment(
    segment_id: str,
    shots: List[Dict[str, Any]],
    output_path: str,
    output_format: str = "horizontal_16_9",
    subtitle_config: Optional[Dict[str, Any]] = None,
    transition_config: Optional[Dict[str, Any]] = None,
    title_config: Optional[Dict[str, Any]] = None,
    bgm_config: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> Dict[str, Any]:
    """
    将一个段落的所有分镜合成为视频。

    参数：
      segment_id: 段落 ID
      shots: 分镜数据列表（含 image_path, audio_path, audio_duration, dialogue, narrator_text 等）
      output_path: 最终视频输出路径
      output_format: 输出格式
      subtitle_config: 字幕配置
      transition_config: 转场配置
      title_config: 片头配置
      bgm_config: 背景音乐配置
      progress_callback: 进度回调函数 callback(step_name, percent)

    返回：
      { video_path, duration, resolution, file_size_mb }
    """
    if not shots:
        raise ValueError("没有分镜数据")

    if subtitle_config is None:
        subtitle_config = {"enabled": True}
    if transition_config is None:
        transition_config = {"type": "fade", "duration": 0.5}
    if title_config is None:
        title_config = {"enabled": False}

    width, height = get_resolution(output_format)
    resolution = f"{width}x{height}"

    # 创建临时工作目录
    work_dir = tempfile.mkdtemp(prefix=f"compose_{segment_id}_")

    try:
        total_steps = 7
        step = 0

        # ── 步骤 1：验证输入文件 ──
        _report(progress_callback, "验证输入文件", step, total_steps)
        for shot in shots:
            if not os.path.exists(shot["image_path"]):
                raise FileNotFoundError(f"分镜图片不存在: {shot['image_path']}")
            if shot.get("audio_path") and not os.path.exists(shot["audio_path"]):
                raise FileNotFoundError(f"分镜音频不存在: {shot['audio_path']}")
        step += 1

        # ── 步骤 2：为每个分镜生成视频片段 ──
        _report(progress_callback, "生成分镜视频片段", step, total_steps)
        fragments = []
        for i, shot in enumerate(shots):
            frag_path = os.path.join(work_dir, f"frag_{i:04d}.mp4")
            audio_dur = shot.get("audio_duration", 0)
            if audio_dur <= 0:
                audio_dur = 5.0
            video_dur = audio_dur + 0.5  # 多半秒缓冲

            _image_to_video(
                image_path=shot["image_path"],
                output_path=frag_path,
                width=width,
                height=height,
                duration=video_dur,
                fps=30,
                ken_burns=True,
            )

            # 如果有音频，合并音频
            if shot.get("audio_path") and os.path.exists(shot["audio_path"]):
                frag_with_audio = os.path.join(work_dir, f"frag_audio_{i:04d}.mp4")
                _merge_audio_to_video(frag_path, shot["audio_path"], frag_with_audio, video_dur)
                fragments.append(frag_with_audio)
            else:
                fragments.append(frag_path)

        step += 1

        # ── 步骤 3：拼接片段（带转场）──
        _report(progress_callback, "拼接视频片段", step, total_steps)
        trans_type = transition_config.get("type", "fade")
        trans_dur = transition_config.get("duration", 0.5)

        if trans_type == "none" or trans_dur <= 0 or len(fragments) == 1:
            concat_path = os.path.join(work_dir, "concat.mp4")
            _concat_videos_simple(fragments, concat_path)
        else:
            concat_path = os.path.join(work_dir, "concat.mp4")
            _concat_videos_with_transition(fragments, concat_path, trans_type, trans_dur)

        step += 1

        # ── 步骤 4：添加片头 ──
        _report(progress_callback, "添加片头", step, total_steps)
        if title_config.get("enabled") and title_config.get("text"):
            title_path = os.path.join(work_dir, "title.mp4")
            generate_title_video(
                text=title_config["text"],
                duration=title_config.get("duration", 3.0),
                output_path=title_path,
                resolution=resolution,
            )
            with_title = os.path.join(work_dir, "with_title.mp4")
            _concat_videos_simple([title_path, concat_path], with_title)
            current_video = with_title
        else:
            current_video = concat_path

        step += 1

        # ── 步骤 5：叠加字幕 ──
        _report(progress_callback, "叠加字幕", step, total_steps)
        if subtitle_config.get("enabled", True):
            # 计算片头偏移量
            title_offset = 0
            if title_config.get("enabled") and title_config.get("text"):
                title_offset = title_config.get("duration", 3.0)

            # 生成字幕（考虑片头偏移）
            adjusted_shots = []
            for shot in shots:
                adj = dict(shot)
                adj["_time_offset"] = title_offset
                adjusted_shots.append(adj)

            ass_path = os.path.join(work_dir, "subs.ass")
            generate_ass(shots, ass_path, subtitle_config)

            with_subs = os.path.join(work_dir, "with_subs.mp4")
            _burn_subtitles(current_video, ass_path, with_subs)
            current_video = with_subs

        step += 1

        # ── 步骤 6：叠加背景音乐 ──
        _report(progress_callback, "叠加背景音乐", step, total_steps)
        if bgm_config and bgm_config.get("enabled") and bgm_config.get("file_path"):
            if os.path.exists(bgm_config["file_path"]):
                with_bgm = os.path.join(work_dir, "with_bgm.mp4")
                # 先提取当前音频
                audio_only = os.path.join(work_dir, "current_audio.aac")
                subprocess.run(
                    ["ffmpeg", "-y", "-i", current_video, "-vn", "-acodec", "aac", audio_only],
                    capture_output=True, check=True,
                )
                # 混合背景音乐
                mixed_audio = os.path.join(work_dir, "mixed_audio.aac")
                mix_with_bgm(audio_only, bgm_config["file_path"], mixed_audio, bgm_config.get("volume", 0.2))
                # 替换音频
                subprocess.run(
                    ["ffmpeg", "-y", "-i", current_video, "-i", mixed_audio,
                     "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0", "-shortest", with_bgm],
                    capture_output=True, check=True,
                )
                current_video = with_bgm

        step += 1

        # ── 步骤 7：输出最终视频 ──
        _report(progress_callback, "输出最终视频", step, total_steps)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy2(current_video, output_path)

        # 获取视频信息
        duration = _get_video_duration(output_path)
        file_size = os.path.getsize(output_path) / (1024 * 1024)

        _report(progress_callback, "完成", total_steps, total_steps)

        return {
            "video_path": output_path,
            "duration": round(duration, 2),
            "resolution": resolution,
            "file_size_mb": round(file_size, 2),
            "shot_count": len(shots),
        }

    finally:
        # 清理临时目录
        try:
            shutil.rmtree(work_dir)
        except OSError:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 内部工具函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _report(callback, step_name, step, total):
    if callback:
        pct = int(step / total * 100)
        callback(step_name, pct)


def _image_to_video(image_path, output_path, width, height, duration, fps=30, ken_burns=True):
    """将静态图片转为视频片段，可选 Ken Burns 效果"""
    # 先用 Pillow 缩放图片到目标分辨率
    img = Image.open(image_path)
    img = img.convert("RGB")

    # 智能裁剪：按目标比例裁剪，然后缩放
    target_ratio = width / height
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # 图片更宽，按高度缩放后裁剪宽度
        new_h = height
        new_w = int(img_ratio * height)
    else:
        # 图片更高，按宽度缩放后裁剪高度
        new_w = width
        new_h = int(width / img_ratio)

    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)  # type: ignore[attr-defined]

    # 居中裁剪
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    img = img.crop((left, top, left + width, top + height))

    resized_path = output_path + ".resized.png"
    img.save(resized_path, "PNG")

    total_frames = int(duration * fps)

    if ken_burns:
        # Ken Burns：缓慢放大效果
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", resized_path,
            "-vf", (
                f"zoompan=z='min(zoom+0.0005,1.15)'"
                f":x='iw/2-(iw/zoom/2)'"
                f":y='ih/2-(ih/zoom/2)'"
                f":d={total_frames}"
                f":s={width}x{height}"
                f":fps={fps}"
            ),
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", resized_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            output_path,
        ]

    subprocess.run(cmd, check=True, capture_output=True)

    # 清理缩放后的临时图片
    try:
        os.unlink(resized_path)
    except OSError:
        pass


def _merge_audio_to_video(video_path, audio_path, output_path, max_duration):
    """将音频合并到视频中"""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-t", str(max_duration),
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _concat_videos_simple(fragments, output_path):
    """简单拼接视频（无转场）"""
    if len(fragments) == 1:
        shutil.copy2(fragments[0], output_path)
        return

    list_path = output_path + ".list.txt"
    with open(list_path, "w") as f:
        for p in fragments:
            f.write(f"file '{os.path.abspath(p)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    try:
        os.unlink(list_path)
    except OSError:
        pass


def _concat_videos_with_transition(fragments, output_path, trans_type, trans_dur):
    """带转场效果拼接视频"""
    if len(fragments) <= 1:
        _concat_videos_simple(fragments, output_path)
        return

    # 获取每个片段的时长
    durations = []
    for frag in fragments:
        dur = _get_video_duration(frag)
        durations.append(dur)

    # 构建 xfade 滤镜链
    n = len(fragments)
    inputs = []
    for frag in fragments:
        inputs.extend(["-i", frag])

    filters = []
    current_label = "[0:v]"

    for i in range(1, n):
        # 计算偏移量：前面所有片段时长之和 - 已消耗的转场时长
        offset = sum(durations[:i]) - trans_dur * i
        if offset < 0:
            offset = 0

        out_label = f"[v{i}]"
        filters.append(
            f"{current_label}[{i}:v]xfade=transition={trans_type}"
            f":duration={trans_dur}:offset={offset:.3f}{out_label}"
        )
        current_label = out_label

    # 音频拼接（简单拼接，不做音频转场）
    audio_inputs = "".join(f"[{i}:a]" for i in range(n))
    audio_filter = f"{audio_inputs}concat=n={n}:v=0:a=1[aout]"

    filter_complex = ";".join(filters) + ";" + audio_filter

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", current_label,
        "-map", "[aout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        # 如果转场失败，回退到简单拼接
        _concat_videos_simple(fragments, output_path)


def _burn_subtitles(video_path, ass_path, output_path):
    """将 ASS 字幕烧录到视频中"""
    # 处理路径中的特殊字符
    safe_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"ass='{safe_ass_path}'",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        # 如果 ASS 字幕失败，尝试用 SRT
        srt_path = ass_path.replace(".ass", ".srt")
        if os.path.exists(srt_path):
            safe_srt = srt_path.replace("\\", "/").replace(":", "\\:")
            cmd_srt = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", f"subtitles='{safe_srt}':force_style='FontSize=24,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2'",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                output_path,
            ]
            subprocess.run(cmd_srt, check=True, capture_output=True)
        else:
            # 都失败则跳过字幕
            shutil.copy2(video_path, output_path)


def _get_video_duration(video_path: str) -> float:
    """获取视频时长"""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 0.0