## 文件 13：dify-config/workflows/workflow-d.md

```markdown
# Workflow-D：确认并合成

## 用途

用户确认所有分镜后，触发视频合成。

## 应用信息

- **名称**：文章转视频 - 确认并合成
- **类型**：工作流编排
- **输入变量**：segment_id, project_id, output_format

## 节点清单

```
[开始] → [HTTP:确认分镜] → [HTTP:获取已确认分镜] → [代码:构造合成参数]
       → [HTTP:调用视频合成] → [HTTP:更新段落状态] → [输出:完成]
```

## 逐步搭建指南

### 节点 1：开始节点

| 变量名 | 类型 | 必填 | 默认值 |
|:---|:---|:---|:---|
| segment_id | 文本字符串 | 是 | - |
| project_id | 文本字符串 | 是 | - |
| output_format | 下拉选项 | 否 | horizontal_16_9 |

---

### 节点 2：HTTP — 确认所有分镜

**PUT** `http://localhost:5005/api/segments/{{segment_id}}/confirm`

---

### 节点 3：HTTP — 获取已确认分镜产物

**GET** `http://localhost:5005/api/segments/{{segment_id}}/shots?status=confirmed`

**输出变量**：`confirmed_response`

---

### 节点 3P：代码 — 构造合成请求体

```python
import json

def main(confirmed_response: str, segment_id: str, output_format: str = "horizontal_16_9") -> dict:
    data = json.loads(confirmed_response)
    shots = data.get("shots", [])

    compose_shots = []
    for i, shot in enumerate(shots):
        compose_shots.append({
            "shot_id": shot.get("id", ""),
            "shot_index": shot.get("shot_index", i + 1),
            "image_path": shot.get("image_path", ""),
            "audio_path": shot.get("audio_path", ""),
            "audio_duration": shot.get("audio_duration", 5.0),
            "dialogue": shot.get("dialogue", ""),
            "narrator_text": shot.get("narrator_text", ""),
            "speaker": shot.get("speaker", ""),
        })

    request_body = {
        "segment_id": segment_id,
        "shots": compose_shots,
        "output_format": output_format,
        "subtitle": {"enabled": True, "font_size": 24},
        "transition": {"type": "fade", "duration": 0.5},
        "title": {"enabled": False},
    }

    return {"compose_body": json.dumps(request_body, ensure_ascii=False)}
```

**输出变量**：`compose_body`

---

### 节点 4：HTTP — 调用视频合成服务

**POST** `http://localhost:5003/api/compositor/segment`
**Headers**：`Content-Type: application/json`
**Body**：`{{compose_body}}`
**超时**：300 秒

**输出变量**：`compose_response`

---

### 节点 4P：代码 — 提取合成结果

```python
import json

def main(compose_response: str) -> dict:
    data = json.loads(compose_response)
    return {
        "video_path": data.get("video_path", ""),
        "video_duration": str(data.get("duration", 0)),
        "file_size": str(data.get("file_size_mb", 0)),
    }
```

---

### 节点 5：HTTP — 更新段落状态

**PUT** `http://localhost:5005/api/segments/{{segment_id}}`
**Body**：
```json
{
  "status": "completed",
  "video_path": "{{video_path}}",
  "video_duration": {{video_duration}}
}
```

---

### 节点 6：输出

**回复内容**：
```
视频合成完成！

视频路径：{{video_path}}
视频时长：{{video_duration}} 秒
文件大小：{{file_size}} MB
```
```

---