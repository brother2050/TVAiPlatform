from typing import List, Tuple


def build_xfade_filter(
    fragments: List[str],
    transition_type: str,
    transition_duration: float,
) -> Tuple[str, List[str]]:
    """
    构建 FFmpeg xfade 转场滤镜链。
    返回 (filter_complex 字符串, 输出标签列表)
    """
    if len(fragments) <= 1:
        return "", ["[0:v]"]

    if transition_type == "none" or transition_duration <= 0:
        # 无转场，直接拼接
        concat_inputs = "".join(f"[{i}:v]" for i in range(len(fragments)))
        return f"{concat_inputs}concat=n={len(fragments)}:v=1:a=0[vout]", ["[vout]"]

    # 计算每个片段的时长（从外部传入更精确，这里用估算）
    # 这里只构建滤镜模板，实际偏移量在 video_builder 中计算
    filters = []
    current = "[0:v]"

    for i in range(1, len(fragments)):
        next_input = f"[{i}:v]"
        output = f"[v{i}]"

        # xfade 偏移量 = 前面所有片段时长之和 - 累积转场时长
        # 具体数值由 video_builder 计算后填入
        filters.append(
            f"{current}{next_input}xfade=transition={transition_type}"
            f":duration={transition_duration}:offset=OFFSET_{i}{output}"
        )
        current = output

    return ";".join(filters), [current]


def get_available_transitions() -> List[str]:
    """返回支持的转场类型列表"""
    return [
        "none",
        "fade",
        "fadeblack",
        "fadewhite",
        "distance",
        "wipeleft",
        "wiperight",
        "wipeup",
        "wipedown",
        "slideleft",
        "slideright",
        "slideup",
        "slidedown",
        "smoothleft",
        "smoothright",
        "smoothup",
        "smoothdown",
        "circlecrop",
        "rectcrop",
        "circleclose",
        "circleopen",
        "horzclose",
        "horzopen",
        "vertclose",
        "vertopen",
        "diagbl",
        "diagbr",
        "diagtl",
        "diagtr",
        "hlslice",
        "hrslice",
        "vuslice",
        "vdslice",
        "dissolve",
        "pixelize",
        "radial",
        "hblur",
        "wipetl",
        "wipetr",
        "wipebl",
        "wipebr",
        "squeezeh",
        "squeezev",
    ]