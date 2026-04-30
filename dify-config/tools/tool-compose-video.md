# 工具 4：compose_video（视频合成）

## 基本信息

- **工具名称**：compose_video
- **描述**：将段落的分镜图片和音频合成为视频
- **请求方式**：POST
- **请求 URL**：`http://localhost:5003/api/compositor/segment`

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| segment_id | string | 是 | - | 段落 ID |
| shots | array | 是 | - | 分镜产物列表 |
| output_format | string | 否 | horizontal_16_9 | 输出格式 |
| subtitle | object | 否 | 见下 | 字幕配置 |
| transition | object | 否 | 见下 | 转场配置 |
| title | object | 否 | 见下 | 片头配置 |
| background_music | object | 否 | null | 背景音乐配置 |

## 请求体示例

```json
{
  "segment_id": "seg_001",
  "shots": [
    {
      "shot_id": "shot_001",
      "shot_index": 1,
      "image_path": "/storage/.../shot_001/v1.png",
      "audio_path": "/storage/.../shot_001.wav",
      "audio_duration": 5.2,
      "dialogue": "",
      "narrator_text": "清晨的阳光透过窗帘。",
      "speaker": ""
    },
    {
      "shot_id": "shot_002",
      "shot_index": 2,
      "image_path": "/storage/.../shot_002/v1.png",
      "audio_path": "/storage/.../shot_002.wav",
      "audio_duration": 3.8,
      "dialogue": "又做那个梦了...",
      "narrator_text": "",
      "speaker": "小明"
    }
  ],
  "output_format": "horizontal_16_9",
  "subtitle": {
    "enabled": true,
    "font_size": 24,
    "font_color": "#FFFFFF",
    "outline_color": "#000000",
    "position": "bottom_center"
  },
  "transition": {
    "type": "fade",
    "duration": 0.5
  },
  "title": {
    "enabled": true,
    "text": "第一段：清晨醒来",
    "duration": 3.0
  }
}
响应格式
{
  "task_id": "compose_abc123",
  "video_path": "/storage/.../seg_001/video.mp4",
  "duration": 32.5,
  "resolution": "1920x1080",
  "file_size_mb": 15.3,
  "shot_count": 6
}
超时设置

建议设置超时时间为 300 秒（5 分钟），视频合成可能耗时较长。