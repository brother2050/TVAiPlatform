
---

## 文件 3：dify-config/tools/tool-generate-speech.md

```markdown
# 工具 2：generate_speech（TTS）

## 基本信息

- **工具名称**：generate_speech
- **描述**：调用 TTS 引擎将文本转为语音
- **请求方式**：POST
- **请求 URL**：根据实际引擎配置

## URL 配置说明

| 引擎 | URL 示例 |
|:---|:---|
| Fish Speech | `http://localhost:8004/tts` |
| CosyVoice | `http://localhost:8005/tts` |
| GPT-SoVITS | `http://localhost:9880/tts` |

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| text | string | 是 | - | 要转语音的文本 |
| speaker | string | 否 | default | 说话人标识 |
| speed | number | 否 | 1.0 | 语速（0.5-2.0） |

## 请求体示例

```json
{
  "text": "这是什么？谁寄来的？",
  "speaker": "speaker_01",
  "speed": 1.0
}
响应格式
{
  "audio_url": "/storage/projects/proj_001/segments/seg_001/shots/shot_003/shot_003.wav",
  "duration": 4.2
}
