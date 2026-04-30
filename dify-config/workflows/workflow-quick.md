## 文件 15：dify-config/workflows/workflow-quick.md

```markdown
# 快速模式：一句话全自动

## 用途

用户输入一段文字（甚至一句话），系统全自动完成全部流程。

## 实现方式

快速模式不是一个独立的工作流，而是 **Workflow-A + Workflow-B + 自动确认 + Workflow-D** 的串联执行。

## 两种实现方案

### 方案 A：串联调用（推荐）

创建一个主工作流，通过 HTTP 请求节点依次调用其他工作流的 API。

```
[开始:输入文字]
  → [LLM:大纲扩写（如果输入很短）]
  → [HTTP:调用 Workflow-A 的逻辑（预处理）]
  → [HTTP:调用 Workflow-B 的逻辑（渲染）]
  → [HTTP:自动确认所有分镜]
  → [HTTP:调用合成服务]
  → [输出:视频路径]
```

### 方案 B：合并为一个大工作流

将所有步骤合并到一个工作流中，适合对 Dify 工作流比较熟悉的用户。

## 方案 A 详细搭建

### 节点 1：开始节点

| 变量名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| input_text | 段落 | 是 | 一段文字或一句话大纲 |
| style_hint | 文本字符串 | 否 | 画风偏好 |

### 节点 2：LLM — 大纲扩写

**条件**：如果 input_text 少于 200 字，先扩写

**系统提示词**：
```
你是一个网文编剧。请将以下简短大纲扩写为一个完整的短篇故事场景（300-800字）。
要求：有具体的场景描写、人物动作、对话。
```

**用户提示词**：`{{input_text}}`

**输出变量**：`expanded_text`

### 节点 2P：代码 — 选择使用原文还是扩写

```python
def main(input_text: str, expanded_text: str = "") -> dict:
    if len(input_text) < 200 and expanded_text:
        return {"final_text": expanded_text}
    return {"final_text": input_text}
```

**输出变量**：`final_text`

### 节点 3：LLM — 生成分镜脚本

直接将 final_text 作为一段来处理（快速模式不拆分多段）。

**系统提示词**：
```
你是一个专业的分镜脚本编剧。将以下文字转化为 4-8 个分镜。
```

**用户提示词**：
```
将以下文字转化为分镜脚本，严格 JSON 输出：
{
  "shots": [
    {
      "shot_index": 1,
      "scene_description": "中文画面描述",
      "prompt": "English prompt for image generation, detailed",
      "negative_prompt": "blurry, low quality, distorted",
      "dialogue": "台词",
      "narrator_text": "旁白",
      "speaker": "说话人",
      "camera": "镜头",
      "characters": ["人物"],
      "duration_hint": 5
    }
  ]
}

文字内容：
{{final_text}}
```

### 节点 3P：代码 — 解析分镜 + 创建项目 + 保存数据

```python
import json
import re
import urllib.request

API_BASE = "http://localhost:5005"

def api_call(method, path, body=None):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def main(shot_result: str, final_text: str) -> dict:
    # 解析分镜
    try:
        json_match = re.search(r'\{[\s\S]*\}', shot_result)
        data = json.loads(json_match.group()) if json_match else json.loads(shot_result)
        shots = data.get("shots", [])
    except:
        return {"status": "error", "message": "分镜解析失败"}

    # 创建项目
    project = api_call("POST", "/api/projects", {
        "name": "快速模式项目",
        "source_text": final_text,
        "split_mode": "auto",
    })
    project_id = project.get("id", "")

    if not project_id:
        return {"status": "error", "message": "项目创建失败"}

    # 保存段落和分镜
    result = api_call("POST", f"/api/projects/{project_id}/segments", {
        "segment_index": 1,
        "title": "快速生成",
        "content": final_text,
        "summary": final_text[:50],
        "shots": shots,
    })

    return {
        "status": "ok",
        "project_id": project_id,
        "segment_id": result.get("segment_id", ""),
        "shot_count": str(len(shots)),
    }
```

### 后续节点

解析出 project_id 和 segment_id 后，通过 HTTP 请求节点：

1. 调用生图引擎为每个分镜生成图片 → 保存
2. 调用 TTS 为每个分镜生成配音 → 保存
3. 自动确认所有分镜
4. 调用合成服务生成视频

这些步骤与 Workflow-B 和 Workflow-D 中的节点相同，可复用。

### 最终输出

```
快速模式完成！

项目 ID：{{project_id}}
视频路径：{{video_path}}
分镜数：{{shot_count}}
```
```

---