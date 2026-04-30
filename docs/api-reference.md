## 文件 17：docs/api-reference.md

```markdown
# API 接口速查

## 项目管理服务（端口 5005）

### 项目

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | /api/projects | 创建项目 |
| GET | /api/projects | 列出项目 |
| GET | /api/projects/{id} | 项目详情 |
| DELETE | /api/projects/{id} | 删除项目 |

### 段落

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | /api/projects/{id}/segments | 保存段落+分镜 |
| GET | /api/segments/{id} | 段落详情 |
| PUT | /api/segments/{id} | 更新段落 |
| PUT | /api/segments/{id}/content | 编辑段落文本 |
| PUT | /api/segments/{id}/confirm | 确认所有分镜 |
| GET | /api/segments/{id}/shots | 查询段落分镜 |
| POST | /api/segments/{id}/recompose | 重新合成 |

### 分镜

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/shots/{id} | 分镜详情 |
| POST | /api/shots/{id}/image | 更新图片 |
| POST | /api/shots/{id}/audio | 更新音频 |
| POST | /api/shots/{id}/regenerate | 重新生成 |
| PUT | /api/shots/{id}/script | 编辑脚本 |
| PUT | /api/shots/{id}/audio_params | 编辑配音参数 |
| POST | /api/shots/{id}/image/upload | 上传图片 |
| POST | /api/shots/{id}/audio/upload | 上传音频 |
| GET | /api/shots/{id}/versions | 历史版本 |

### 批量处理

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/projects/{id}/pending | 查询待处理项 |
| POST | /api/projects/{id}/process-pending | 批量处理 |

### 健康检测

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /health | 健康状态 |

---

## 视频合成服务（端口 5003）

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | /api/compositor/segment | 同步合成 |
| POST | /api/compositor/segment/async | 异步合成 |
| GET | /api/compositor/status/{task_id} | 查询进度 |
| GET | /health | 健康状态 |

---

## 请求/响应示例

### 创建项目

```bash
curl -X POST http://localhost:5005/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的小说",
    "author": "张三",
    "source_text": "清晨的阳光...",
    "split_mode": "auto",
    "style_hint": "国漫水墨风格"
  }'
```

### 保存段落和分镜

```bash
curl -X POST http://localhost:5005/api/projects/proj_abc123/segments \
  -H "Content-Type: application/json" \
  -d '{
    "segment_index": 1,
    "title": "清晨醒来",
    "content": "清晨的阳光透过窗帘...",
    "summary": "主角清晨醒来",
    "shots": [
      {
        "shot_index": 1,
        "scene_description": "清晨卧室",
        "prompt": "A bedroom in early morning, sunlight through curtains",
        "negative_prompt": "blurry, low quality",
        "dialogue": "",
        "narrator_text": "清晨的阳光...",
        "speaker": "",
        "camera": "中景",
        "characters": ["小明"],
        "duration_hint": 5
      }
    ]
  }'
```

### 合成视频

```bash
curl -X POST http://localhost:5003/api/compositor/segment \
  -H "Content-Type: application/json" \
  -d '{
    "segment_id": "seg_abc123",
    "shots": [
      {
        "shot_id": "shot_001",
        "shot_index": 1,
        "image_path": "/storage/.../v1.png",
        "audio_path": "/storage/.../shot_001.wav",
        "audio_duration": 5.2,
        "dialogue": "",
        "narrator_text": "清晨的阳光...",
        "speaker": ""
      }
    ],
    "output_format": "horizontal_16_9",
    "subtitle": {"enabled": true},
    "transition": {"type": "fade", "duration": 0.5}
  }'
```
```

---