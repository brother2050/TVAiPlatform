## 文件 14：dify-config/workflows/workflow-e.md

```markdown
# Workflow-E：合成输出（独立合成）

## 用途

独立的合成工作流，供需要单独重新合成时使用（如调整合成参数后）。

## 与 Workflow-D 的区别

- Workflow-D 包含"确认分镜"步骤，适合首次合成
- Workflow-E 不包含确认步骤，适合重新合成

## 应用信息

- **名称**：文章转视频 - 合成输出
- **类型**：工作流编排
- **输入变量**：segment_id, output_format, transition_type, transition_duration, title_text, subtitle_enabled

## 节点清单

```
[开始] → [HTTP:获取分镜产物] → [代码:构造合成参数] → [HTTP:调用合成] → [HTTP:更新状态] → [输出]
```

## 逐步搭建指南

### 节点 1：开始节点

| 变量名 | 类型 | 必填 | 默认值 |
|:---|:---|:---|:---|
| segment_id | 文本字符串 | 是 | - |
| output_format | 下拉选项 | 否 | horizontal_16_9 |
| transition_type | 文本字符串 | 否 | fade |
| transition_duration | 数字 | 否 | 0.5 |
| title_text | 文本字符串 | 否 | （空） |
| subtitle_enabled | 下拉选项 | 否 | true |

后续节点与 Workflow-D 的节点 3 到节点 6 相同，区别在于合成参数从输入变量中读取。

构造合成参数的代码：
```python
import json

def main(confirmed_response: str, segment_id: str, output_format: str = "horizontal_16_9",
         transition_type: str = "fade", transition_duration: float = 0.5,
         title_text: str = "", subtitle_enabled: str = "true") -> dict:

    data = json.loads(confirmed_response)
    shots = data.get("shots", [])

    compose_shots = []
    for shot in shots:
        compose_shots.append({
            "shot_id": shot.get("id", ""),
            "shot_index": shot.get("shot_index", 0),
            "image_path": shot.get("image_path", ""),
            "audio_path": shot.get("audio_path", ""),
            "audio_duration": shot.get("audio_duration", 5.0),
            "dialogue": shot.get("dialogue", ""),
            "narrator_text": shot.get("narrator_text", ""),
            "speaker": shot.get("speaker", ""),
        })

    title_config = {"enabled": bool(title_text), "text": title_text, "duration": 3.0}

    request_body = {
        "segment_id": segment_id,
        "shots": compose_shots,
        "output_format": output_format,
        "subtitle": {"enabled": subtitle_enabled == "true", "font_size": 24},
        "transition": {"type": transition_type, "duration": transition_duration},
        "title": title_config,
    }

    return {"compose_body": json.dumps(request_body, ensure_ascii=False)}
```
```

---