
---

## 文件 11：dify-config/workflows/workflow-b.md

```markdown
# Workflow-B：单段渲染

## 用途

对一个段落的所有分镜执行生图和 TTS。

## 应用信息

- **名称**：文章转视频 - 单段渲染
- **类型**：工作流编排
- **输入变量**：segment_id, project_id

## 节点清单

[开始] → [HTTP:获取段落分镜] → [代码:解析分镜列表]
→ [循环:遍历分镜]
→   [代码:构造提示词] → [HTTP:调用生图] → [HTTP:保存图片]
→   [条件:有台词?] → [HTTP:调用TTS] → [HTTP:保存音频]
→ [HTTP:更新段落状态] → [输出:完成]


## 逐步搭建指南

### 节点 1：开始节点

| 变量名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| segment_id | 文本字符串 | 是 | 段落 ID |
| project_id | 文本字符串 | 是 | 项目 ID |

---

### 节点 2：HTTP 请求 — 获取段落分镜

**方法**：GET
**URL**：`http://localhost:5005/api/segments/{{segment_id}}`

**输出变量**：`segment_response`

---

### 节点 2P：代码 — 解析分镜列表

```python
import json

def main(segment_response: str) -> dict:
    data = json.loads(segment_response)
    shots = data.get("shots", [])
    title = data.get("title", "")
    return {
        "shots_list": shots,
        "segment_title": title,
        "shot_count": str(len(shots)),
    }
输出变量：shots_list, segment_title, shot_count
节点 3：迭代 — 遍历分镜

迭代输入：shots_list

循环体内：

节点 3.1：代码 — 构造生图提示词
def main(item: dict, style_hint: str = "") -> dict:
    prompt = item.get("prompt", "")
    if style_hint:
        prompt = f"{prompt}, {style_hint}"
    return {
        "final_prompt": prompt,
        "final_negative": item.get("negative_prompt", "blurry, low quality"),
    }
    注意：style_hint 需要从开始节点透传下来。如果 Dify 迭代节点不支持外部变量，可以在开始节点的输入中加入 style_hint。


节点 3.2：HTTP 请求 — 调用生图引擎

方法：POST
URL：http://localhost:8188/api/prompt（根据实际引擎修改）
Body：
{
  "prompt": "{{final_prompt}}",
  "negative_prompt": "{{final_negative}}",
  "width": 1024,
  "height": 576,
  "steps": 30,
  "seed": -1
}
超时：120 秒

输出变量：image_response

节点 3.2P：代码 — 提取图片路径
import json

def main(image_response: str) -> dict:
    data = json.loads(image_response)
    return {"image_path": data.get("image_url", "")}

节点 3.3：HTTP 请求 — 保存分镜图片

方法：POST
URL：http://localhost:5005/api/shots/{{item.id}}/imageBody：
{
  "image_path": "{{image_path}}"
}

条件：
{{item.dialogue}} 不为空 或 {{item.narrator_text}} 不为空
    是 → 连接到 TTS 节点
    否 → 跳过 TTS，连接到循环下一个


节点 3.5：HTTP 请求 — 调用 TTS

方法：POST
URL：http://localhost:8004/tts（根据实际引擎修改）
Body：
{
  "text": "{{item.dialogue}}{{item.narrator_text}}",
  "speaker": "{{item.speaker}}",
  "speed": 1.0
}
超时：30 秒

输出变量：tts_response

节点 3.5P：代码 — 提取音频信息
import json

def main(tts_response: str) -> dict:
    data = json.loads(tts_response)
    return {
        "audio_path": data.get("audio_url", ""),
        "audio_duration": str(data.get("duration", 5.0)),
    }
节点 3.6：HTTP 请求 — 保存配音

方法：POST
URL：http://localhost:5005/api/shots/{{item.id}}/audioBody：
{
  "audio_path": "{{audio_path}}",
  "duration": {{audio_duration}}
}
节点 4：HTTP 请求 — 更新段落状态

方法：PUT
URL：http://localhost:5005/api/segments/{{segment_id}}Body：
{
  "status": "rendered"
}
Part 3：Dify 配置 + 文档


交付范围

text

text

Part 3 包含：
  □ dify-config/tools/README.md                          工具配置总览
  □ dify-config/tools/tool-generate-image.md             生图工具配置
  □ dify-config/tools/tool-generate-speech.md            TTS 工具配置
  □ dify-config/tools/tool-save-project-data.md          项目数据工具配置
  □ dify-config/tools/tool-compose-video.md              视频合成工具配置
  □ dify-config/tools/tool-regenerate-shot.md            分镜重生成工具配置
  □ dify-config/tools/tool-edit-shot-script.md           分镜编辑工具配置
  □ dify-config/tools/tool-process-pending.md            批量处理工具配置
  □ dify-config/workflows/README.md                      工作流总览
  □ dify-config/workflows/workflow-a.md                  Workflow-A 详细搭建指南
  □ dify-config/workflows/workflow-b.md                  Workflow-B 详细搭建指南
  □ dify-config/workflows/workflow-c.md                  Workflow-C 详细搭建指南
  □ dify-config/workflows/workflow-d.md                  Workflow-D 详细搭建指南
  □ dify-config/workflows/workflow-e.md                  Workflow-E 详细搭建指南
  □ dify-config/workflows/workflow-quick.md              快速模式搭建指南
  □ docs/deployment.md                                   部署指南
  □ docs/api-reference.md                                API 速查
  □ docs/troubleshooting.md                              问题排查
  □ README.md                                            项目说明



文件 1：dify-config/tools/README.md

markdown

markdown

# Dify 自定义工具配置总览

## 概述

本项目需要在 Dify 中注册 7 个自定义工具。这些工具是 Dify 工作流中调用二次开发服务的桥梁。

在 Dify 界面中操作路径：**工具 → 自定义工具 → 创建自定义工具**

## 工具清单

| 序号 | 工具名称 | 调用目标 | 对应文档 |
|:---|:---|:---|:---|
| 1 | generate_image | 生图引擎 | tool-generate-image.md |
| 2 | generate_speech | TTS 引擎 | tool-generate-speech.md |
| 3 | save_project_data | 项目管理服务 | tool-save-project-data.md |
| 4 | compose_video | 视频合成服务 | tool-compose-video.md |
| 5 | regenerate_shot | 项目管理服务 | tool-regenerate-shot.md |
| 6 | edit_shot_script | 项目管理服务 | tool-edit-shot-script.md |
| 7 | process_pending | 项目管理服务 | tool-process-pending.md |

## 创建步骤

1. 打开 Dify 界面
2. 左侧菜单 → **工具**
3. 点击 **自定义** 标签页
4. 点击 **创建自定义工具**
5. 按各工具文档填写名称、描述、请求方式、URL、参数
6. 保存后点击 **测试** 验证连通性
7. 重复以上步骤创建全部 7 个工具

## 通用注意事项

- 工具 URL 中的 `localhost` 需要根据实际部署地址修改
- 如果 Dify 运行在 Docker 中，`localhost` 需改为 `host.docker.internal` 或宿主机 IP
- 所有工具的响应格式必须是 JSON
- 建议每个工具创建后都先手动测试一次



文件 2：dify-config/tools/tool-generate-image.md

markdown

markdown

# 工具 1：generate_image（生图）

## 基本信息

- **工具名称**：generate_image
- **描述**：调用外部生图引擎（如 ComfyUI / SD WebUI）生成图片
- **请求方式**：POST
- **请求 URL**：根据实际引擎配置

## URL 配置说明

不同引擎的 URL 不同：

| 引擎 | URL 示例 |
|:---|:---|
| ComfyUI | `http://localhost:8188/api/prompt` |
| SD WebUI | `http://localhost:7860/sdapi/v1/txt2img` |
| 自定义服务 | `http://localhost:8000/generate` |

> 注意：由于不同引擎的 API 格式差异较大，建议在引擎前面加一个薄适配层（Python 脚本），统一输入输出格式。或者直接使用 Dify 的 HTTP 请求节点，在节点内用代码做格式转换。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| prompt | string | 是 | - | 生图提示词（英文） |
| negative_prompt | string | 否 | blurry, low quality | 负面提示词 |
| width | number | 否 | 1024 | 图片宽度 |
| height | number | 否 | 576 | 图片高度 |
| steps | number | 否 | 30 | 采样步数 |
| seed | number | 否 | -1 | 随机种子（-1 为随机） |

## 请求体示例

```json
{
  "prompt": "A young man sitting at office desk, opening a mysterious letter, warm lighting, detailed, cinematic",
  "negative_prompt": "blurry, low quality, distorted, deformed, extra limbs",
  "width": 1024,
  "height": 576,
  "steps": 30,
  "seed": -1
}


响应格式

json

json

{
  "image_url": "/storage/projects/proj_001/segments/seg_001/shots/shot_001/v1.png",
  "seed": 12345
}


适配层建议

如果直接对接引擎 API 格式不匹配，可以写一个薄适配层：

text

text

Dify Tool → http://localhost:5001/api/adapter/image → 引擎 API


适配层接收统一格式的请求，转换为引擎特定格式，再将引擎响应转回统一格式。
text

text


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

json

json

{
  "audio_url": "/storage/projects/proj_001/segments/seg_001/shots/shot_003/shot_003.wav",
  "duration": 4.2
}

text

text


---

## 文件 4：dify-config/tools/tool-save-project-data.md

```markdown
# 工具 3：save_project_data（项目数据存储）

## 基本信息

- **工具名称**：save_project_data
- **描述**：将项目、段落、分镜数据保存到数据库
- **请求方式**：POST
- **请求 URL**：`http://localhost:5005/api/projects`

> 此工具是项目管理服务 API 的封装，Dify 工作流中通过此工具读写项目数据。

## 实际使用建议

由于项目管理服务已有完整的 REST API，Dify 工作流中建议直接使用 **HTTP 请求节点** 调用对应接口，而非封装为单一工具。

常用接口对照：

| 工作流中的操作 | HTTP 方法 | 接口 |
|:---|:---|:---|
| 创建项目 | POST | /api/projects |
| 保存段落和分镜 | POST | /api/projects/{id}/segments |
| 更新分镜图片 | POST | /api/shots/{id}/image |
| 更新分镜音频 | POST | /api/shots/{id}/audio |
| 查询段落分镜 | GET | /api/segments/{id}/shots?status=confirmed |
| 确认分镜 | PUT | /api/segments/{id}/confirm |

## 如果仍要注册为工具

可以将最常用的操作封装：

### 操作 A：创建项目

- **URL**：`http://localhost:5005/api/projects`
- **方法**：POST
- **参数**：name, source_text, split_mode, style_hint

### 操作 B：保存段落

- **URL**：`http://localhost:5005/api/projects/{project_id}/segments`
- **方法**：POST
- **参数**：segment_index, title, content, summary, shots（JSON 数组）



文件 5：dify-config/tools/tool-compose-video.md

markdown

markdown

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

json

json

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
text

text


---

## 文件 6：dify-config/tools/tool-regenerate-shot.md

```markdown
# 工具 5：regenerate_shot（分镜重生成）

## 基本信息

- **工具名称**：regenerate_shot
- **描述**：重新生成分镜图片（原词重生成或修改后重生成）
- **请求方式**：POST
- **请求 URL**：`http://localhost:5005/api/shots/{shot_id}/regenerate`

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| action | string | 是 | regenerate | 操作类型：regenerate / edit_and_regenerate |
| new_prompt | string | 否 | - | 修改后的提示词（edit 模式） |
| new_negative_prompt | string | 否 | - | 修改后的负面提示词 |
| new_description | string | 否 | - | 修改后的画面描述 |

## 请求体示例（原词重生成）

```json
{
  "action": "regenerate"
}


请求体示例（修改后重生成）

json

json

{
  "action": "edit_and_regenerate",
  "new_prompt": "A young man sitting at office desk, opening a mysterious letter, red desk lamp, warm lighting",
  "new_negative_prompt": "blurry, low quality, deformed"
}


响应格式

json

json

{
  "shot_id": "shot_003",
  "action": "regenerate",
  "prompt": "A young man sitting at office desk...",
  "negative_prompt": "blurry, low quality...",
  "version": 2,
  "message": "已标记为待重新生成"
}


工作流中的使用方式

此工具返回后，Dify 工作流需要再调用 generate_image 工具执行实际生图，然后调用 save_project_data 的图片更新接口保存结果。
text

text


---

## 文件 7：dify-config/tools/tool-edit-shot-script.md

```markdown
# 工具 6：edit_shot_script（分镜脚本编辑）

## 基本信息

- **工具名称**：edit_shot_script
- **描述**：编辑分镜脚本字段，自动判断需要重新生成的部分
- **请求方式**：PUT
- **请求 URL**：`http://localhost:5005/api/shots/{shot_id}/script`

## 请求参数

所有参数均为可选，只传需要修改的字段。

| 参数名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| scene_description | string | 否 | 画面描述 |
| prompt | string | 否 | 生图提示词 |
| negative_prompt | string | 否 | 负面提示词 |
| dialogue | string | 否 | 台词 |
| narrator_text | string | 否 | 旁白 |
| speaker | string | 否 | 说话人 |
| camera | string | 否 | 镜头指示 |

## 请求体示例

```json
{
  "dialogue": "这封信到底是谁寄的？",
  "prompt": "A young man at desk reading letter with red lamp, cinematic lighting"
}


响应格式

json

json

{
  "shot_id": "shot_003",
  "changed_fields": ["dialogue", "prompt"],
  "need_regenerate_image": true,
  "need_regenerate_audio": true,
  "action_required": "regenerate_图片_and_配音",
  "message": "dialogue和prompt已修改，需要重新生成图片和配音"
}

text

text


---

## 文件 8：dify-config/tools/tool-process-pending.md

```markdown
# 工具 7：process_pending（批量处理）

## 基本信息

- **工具名称**：process_pending
- **描述**：批量处理项目中所有待更新的图片、配音和视频合成任务
- **请求方式**：POST
- **请求 URL**：`http://localhost:5005/api/projects/{project_id}/process-pending`

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| scope | string | 否 | all | 处理范围：all / segment:{id} / shot:{id} |

## 请求体示例

```json
{
  "scope": "all"
}


响应格式

json

json

{
  "project_id": "proj_001",
  "pending_image_tasks": 5,
  "pending_audio_tasks": 3,
  "pending_compose_tasks": 2,
  "total_tasks": 10,
  "estimated_time_seconds": 210,
  "message": "已提交 10 个任务到处理队列"
}

text

text


---

## 文件 9：dify-config/workflows/README.md

```markdown
# Dify 工作流搭建指南

## 概述

本项目包含 6 个工作流，需要在 Dify 中逐一创建。

| 工作流 | 用途 | 应用类型 | 文档 |
|:---|:---|:---|:---|
| Workflow-A | 文本预处理（含拆分） | 工作流编排 | workflow-a.md |
| Workflow-B | 单段渲染（生图+TTS） | 工作流编排 | workflow-b.md |
| Workflow-C | 图片审核与重生成 | 工作流编排 | workflow-c.md |
| Workflow-D | 确认并合成 | 工作流编排 | workflow-d.md |
| Workflow-E | 合成输出 | 工作流编排 | workflow-e.md |
| 快速模式 | 一句话全自动 | 工作流编排 | workflow-quick.md |

## 创建步骤

1. Dify 界面 → **工作室** → **创建应用**
2. 选择 **工作流编排**
3. 填写应用名称和描述
4. 进入工作流编辑器
5. 按各工作流文档逐步添加节点、配置参数、连接节点
6. 保存并测试

## 通用配置

### LLM 模型选择

在每个 LLM 节点中：
- **模型**：选择已配置的 LLM（如 DeepSeek / Qwen）
- **温度**：0.3（文本分析类任务）或 0.7（创意生成类任务）
- **最大 Token**：4096（分镜生成）或 8192（长文切分）

### HTTP 请求节点配置

在每个 HTTP 请求节点中：
- **URL**：填写实际的服务地址
- **超时**：普通请求 30 秒，生图 120 秒，视频合成 300 秒
- **错误处理**：选择"继续执行"或"失败终止"根据业务需要

### 变量传递

Dify 工作流中节点间通过变量传递数据：
- 上游节点的输出变量名需要与下游节点的输入变量名匹配
- 使用 `{{变量名}}` 语法引用变量



文件 10：dify-config/workflows/workflow-a.md

markdown

markdown

# Workflow-A：文本预处理（含拆分）

## 用途

接收用户输入的文本，执行拆分（自动/手动），生成分镜脚本，保存到数据库。

## 应用信息

- **名称**：文章转视频 - 文本预处理
- **类型**：工作流编排
- **输入变量**：input_text, split_mode, project_name, style_hint

## 节点清单与连接顺序

[开始] → [条件分支:拆分模式] → [自动拆分LLM / 手动切分代码]
→ [代码:解析结果] → [条件:解析成功?]
→ [HTTP:创建项目] → [循环:遍历段落]
→   [LLM:生成分镜] → [代码:解析分镜] → [HTTP:保存段落分镜]
→ [输出:完成]
text

text


## 逐步搭建指南

### 节点 1：开始节点

**类型**：开始

**配置输入变量**：

| 变量名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| input_text | 段落 | 是 | 用户输入的全文 |
| split_mode | 下拉选项 | 是 | 选项值：auto, manual |
| project_name | 文本字符串 | 否 | 默认值：未命名项目 |
| style_hint | 文本字符串 | 否 | 画风偏好 |

---

### 节点 2：条件分支

**类型**：IF/ELSE

**条件**：

{{split_mode}} 等于 auto
text

text


- 是 → 连接到节点 3A（自动拆分 LLM）
- 否 → 连接到节点 3B（手动切分代码）

---

### 节点 3A：LLM — 自动拆分

**类型**：LLM

**模型**：选择已配置的 LLM

**系统提示词**：

你是一个专业的文章结构分析师。你的任务是将长文按自然段落或场景切分。

切分原则：

    1.每段包含一个完整场景或情节片段
    2.每段 200-800 字，太长继续拆
    3.在场景切换、时间跳跃、地点变化处切分
    4.保持对话完整性
    5.如有明确章节标记，优先按章节切分

text

text


**用户提示词**：

请将以下文章切分为段落，严格按 JSON 格式输出，不要输出任何其他内容：

{
"segments": [
{
"index": 1,
"title": "段落标题",
"content": "段落正文",
"summary": "一句话概括"
}
]
}

文章内容：
{{input_text}}
text

text


**输出变量名**：`split_result`

**连接到**：节点 4A

---

### 节点 4A：代码 — 解析自动拆分结果

**类型**：代码执行

**输入变量**：`split_result`（来自节点 3A）

**Python 代码**：
```python
import json
import re

def main(split_result: str) -> dict:
    try:
        # 尝试从文本中提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', split_result)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(split_result)

        segments = data.get("segments", [])
        if not segments:
            return {"segments_json": "[]", "parse_success": "false", "segment_count": "0"}

        # 校验并补全字段
        for seg in segments:
            seg.setdefault("index", 0)
            seg.setdefault("title", "未命名段落")
            seg.setdefault("content", "")
            seg.setdefault("summary", "")

        return {
            "segments_json": json.dumps(segments, ensure_ascii=False),
            "parse_success": "true",
            "segment_count": str(len(segments)),
        }
    except Exception as e:
        return {
            "segments_json": "[]",
            "parse_success": "false",
            "segment_count": "0",
        }


输出变量：segments_json, parse_success, segment_count

连接到：节点 5（汇合点）


节点 3B：代码 — 手动标记切分

类型：代码执行

输入变量：input_text

Python 代码：
python

python

import re
import json

def main(input_text: str) -> dict:
    # 查找分割标记
    pattern = r'===$$([^$$]*)\]===|===SPLIT==='
    parts = re.split(pattern, input_text)

    segments = []
    index = 1
    i = 0
    current_title = ""

    while i < len(parts):
        if parts[i] is None:
            i += 1
            continue

        # 检查是否是标题（正则分组捕获的标题）
        if i % 2 == 1:
            current_title = parts[i] if parts[i] else ""
            i += 1
            continue

        content = parts[i].strip()
        if content:
            title = current_title if current_title else f"段落 {index}"
            segments.append({
                "index": index,
                "title": title,
                "content": content,
                "summary": content[:50] + "..." if len(content) > 50 else content,
            })
            index += 1
            current_title = ""

        i += 1

    success = len(segments) > 0
    return {
        "segments_json": json.dumps(segments, ensure_ascii=False),
        "parse_success": "true" if success else "false",
        "segment_count": str(len(segments)),
    }


输出变量：segments_json, parse_success, segment_count

连接到：节点 5（汇合点）


节点 5：条件分支 — 检查解析结果

类型：IF/ELSE

条件：
text

text

{{parse_success}} 等于 true


    是 → 连接到节点 6（创建项目）
    否 → 连接到节点 5E（错误提示）



节点 5E：直接回复 — 错误提示

类型：直接回复（结束节点）

回复内容：
text

text

文本解析失败。请检查：
- 自动模式：确保文本长度大于 100 字
- 手动模式：确保使用 ===SPLIT=== 或 ===[标题]=== 标记分割



节点 6：HTTP 请求 — 创建项目

类型：HTTP 请求

配置：

    方法：POST
    URL：http://localhost:5005/api/projects
    Headers：Content-Type: application/json
    Body（JSON）：

json

json

{
  "name": "{{project_name}}",
  "source_text": "{{input_text}}",
  "split_mode": "{{split_mode}}",
  "style_hint": "{{style_hint}}"
}


输出变量：project_response

后处理：在"高级设置"中配置输出变量提取，或者在下一个节点用代码解析。

添加一个代码节点 6P 解析 project_id：
python

python

import json

def main(project_response: str) -> dict:
    try:
        data = json.loads(project_response)
        return {"project_id": data.get("id", "")}
    except:
        return {"project_id": ""}


输出变量：project_id

连接到：节点 7（循环）


节点 7：循环 — 遍历每个段落

类型：迭代（Iteration）

输入变量：segments_json

    注意：Dify 的迭代节点需要输入为数组类型。由于 segments_json 是字符串，需要先用代码节点转为数组。


在循环前添加代码节点 7P：
python

python

import json

def main(segments_json: str) -> dict:
    segments = json.loads(segments_json)
    return {"segment_list": segments}


输出变量：segment_list

迭代输入：segment_list

循环体内节点：

节点 7.1：LLM — 生成分镜脚本

类型：LLM

系统提示词：
text

text

你是一个专业的分镜脚本编剧。你将把一段文字转化为可视化的分镜脚本。
每个分镜代表一个画面，包含画面描述、生图提示词、台词或旁白、镜头指示。


用户提示词：
text

text

请将以下段落转化为分镜脚本。每个分镜代表一个画面。
一段文字通常拆分为 3-8 个分镜。

段落标题：{{item.title}}
段落内容：{{item.content}}

严格按 JSON 格式输出，不要输出任何其他内容：
{
  "shots": [
    {
      "shot_index": 1,
      "scene_description": "画面场景的中文描述",
      "prompt": "English prompt for image generation, detailed, including character appearance, scene, lighting, mood",
      "negative_prompt": "blurry, low quality, distorted, deformed",
      "dialogue": "角色台词（旁白则留空）",
      "narrator_text": "旁白文字（有台词则留空）",
      "speaker": "说话人姓名",
      "camera": "近景/中景/远景/特写/俯拍",
      "characters": ["出场人物"],
      "duration_hint": 5
    }
  ]
}


输出变量：shot_result

节点 7.2：代码 — 解析分镜脚本

类型：代码执行

输入变量：shot_result

Python 代码：
python

python

import json
import re

def main(shot_result: str) -> dict:
    try:
        json_match = re.search(r'\{[\s\S]*\}', shot_result)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(shot_result)

        shots = data.get("shots", [])
        for shot in shots:
            shot.setdefault("shot_index", 0)
            shot.setdefault("scene_description", "")
            shot.setdefault("prompt", "")
            shot.setdefault("negative_prompt", "blurry, low quality, distorted, deformed")
            shot.setdefault("dialogue", "")
            shot.setdefault("narrator_text", "")
            shot.setdefault("speaker", "")
            shot.setdefault("camera", "")
            shot.setdefault("characters", [])
            shot.setdefault("duration_hint", 5)

        return {
            "shots_json": json.dumps(shots, ensure_ascii=False),
            "shot_count": str(len(shots)),
        }
    except Exception as e:
        return {"shots_json": "[]", "shot_count": "0"}


输出变量：shots_json, shot_count

节点 7.3：HTTP 请求 — 保存段落和分镜

类型：HTTP 请求

方法：POST
URL：http://localhost:5005/api/projects/{{project_id}}/segmentsBody：
json

json

{
  "segment_index": {{item.index}},
  "title": "{{item.title}}",
  "content": "{{item.content}}",
  "summary": "{{item.summary}}",
  "shots": {{shots_json}}
}



节点 8：输出 — 预处理完成

类型：直接回复（结束节点）

回复内容：
text

text

文本预处理完成！

项目名称：{{project_name}}
段落数量：{{segment_count}}
项目 ID：{{project_id}}

请在项目管理服务中查看详细信息，然后继续执行渲染。

text

text


---

## 文件 11：dify-config/workflows/workflow-b.md

```markdown
# Workflow-B：单段渲染

## 用途

对一个段落的所有分镜执行生图和 TTS。

## 应用信息

- **名称**：文章转视频 - 单段渲染
- **类型**：工作流编排
- **输入变量**：segment_id, project_id

## 节点清单

[开始] → [HTTP:获取段落分镜] → [代码:解析分镜列表]
→ [循环:遍历分镜]
→   [代码:构造提示词] → [HTTP:调用生图] → [HTTP:保存图片]
→   [条件:有台词?] → [HTTP:调用TTS] → [HTTP:保存音频]
→ [HTTP:更新段落状态] → [输出:完成]
text

text


## 逐步搭建指南

### 节点 1：开始节点

| 变量名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| segment_id | 文本字符串 | 是 | 段落 ID |
| project_id | 文本字符串 | 是 | 项目 ID |

---

### 节点 2：HTTP 请求 — 获取段落分镜

**方法**：GET
**URL**：`http://localhost:5005/api/segments/{{segment_id}}`

**输出变量**：`segment_response`

---

### 节点 2P：代码 — 解析分镜列表

```python
import json

def main(segment_response: str) -> dict:
    data = json.loads(segment_response)
    shots = data.get("shots", [])
    title = data.get("title", "")
    return {
        "shots_list": shots,
        "segment_title": title,
        "shot_count": str(len(shots)),
    }


输出变量：shots_list, segment_title, shot_count


节点 3：迭代 — 遍历分镜

迭代输入：shots_list

循环体内：

节点 3.1：代码 — 构造生图提示词

python

python

def main(item: dict, style_hint: str = "") -> dict:
    prompt = item.get("prompt", "")
    if style_hint:
        prompt = f"{prompt}, {style_hint}"
    return {
        "final_prompt": prompt,
        "final_negative": item.get("negative_prompt", "blurry, low quality"),
    }


    注意：style_hint 需要从开始节点透传下来。如果 Dify 迭代节点不支持外部变量，可以在开始节点的输入中加入 style_hint。


节点 3.2：HTTP 请求 — 调用生图引擎

方法：POST
URL：http://localhost:8188/api/prompt（根据实际引擎修改）
Body：
json

json

{
  "prompt": "{{final_prompt}}",
  "negative_prompt": "{{final_negative}}",
  "width": 1024,
  "height": 576,
  "steps": 30,
  "seed": -1
}

超时：120 秒

输出变量：image_response

节点 3.2P：代码 — 提取图片路径

python

python

import json

def main(image_response: str) -> dict:
    data = json.loads(image_response)
    return {"image_path": data.get("image_url", "")}


节点 3.3：HTTP 请求 — 保存分镜图片

方法：POST
URL：http://localhost:5005/api/shots/{{item.id}}/imageBody：
json

json

{
  "image_path": "{{image_path}}"
}


节点 3.4：条件分支 — 是否有台词或旁白

条件：
text

text

{{item.dialogue}} 不为空 或 {{item.narrator_text}} 不为空


    是 → 连接到 TTS 节点
    否 → 跳过 TTS，连接到循环下一个


节点 3.5：HTTP 请求 — 调用 TTS

方法：POST
URL：http://localhost:8004/tts（根据实际引擎修改）
Body：
json

json

{
  "text": "{{item.dialogue}}{{item.narrator_text}}",
  "speaker": "{{item.speaker}}",
  "speed": 1.0
}

超时：30 秒

输出变量：tts_response

节点 3.5P：代码 — 提取音频信息

python

python

import json

def main(tts_response: str) -> dict:
    data = json.loads(tts_response)
    return {
        "audio_path": data.get("audio_url", ""),
        "audio_duration": str(data.get("duration", 5.0)),
    }


节点 3.6：HTTP 请求 — 保存配音

方法：POST
URL：http://localhost:5005/api/shots/{{item.id}}/audioBody：
json

json

{
  "audio_path": "{{audio_path}}",
  "duration": {{audio_duration}}
}



节点 4：HTTP 请求 — 更新段落状态

方法：PUT
URL：http://localhost:5005/api/segments/{{segment_id}}Body：
json

json

{
  "status": "rendered"
}



节点 5：输出

回复内容：
段落渲染完成！
段落：{{segment_title}}
分镜数：{{shot_count}}
