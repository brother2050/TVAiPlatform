
## 文件 12：dify-config/workflows/workflow-c.md

```markdown
# Workflow-C：图片审核与重生成

## 用途

用户对不满意的分镜图片执行重新生成、修改后重生成或上传替换。

## 应用信息

- **名称**：文章转视频 - 图片审核重生成
- **类型**：工作流编排
- **输入变量**：shot_id, action, new_prompt, new_negative_prompt, new_description

## 节点清单

```
[开始] → [条件:action类型]
       → [分支A:原词重生成] → [HTTP:获取分镜] → [HTTP:调用生图] → [HTTP:保存图片]
       → [分支B:修改后重生成] → [代码:构造新提示词] → [HTTP:调用生图] → [HTTP:保存图片]
       → [分支C:仅标记] → [HTTP:标记待重生成]
       → [输出:结果]
```

## 逐步搭建指南

### 节点 1：开始节点

| 变量名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| shot_id | 文本字符串 | 是 | 分镜 ID |
| action | 下拉选项 | 是 | 选项：regenerate, edit_and_regenerate |
| new_prompt | 文本字符串 | 否 | 修改后的提示词 |
| new_negative_prompt | 文本字符串 | 否 | 修改后的负面提示词 |
| new_description | 文本字符串 | 否 | 修改后的画面描述 |

---

### 节点 2：条件分支

**条件**：`{{action}} 等于 regenerate`

- 是 → 分支 A
- 否 → 分支 B

---

### 分支 A：原词重生成

#### 节点 A1：HTTP — 获取当前分镜数据

**GET** `http://localhost:5005/api/shots/{{shot_id}}`

#### 节点 A1P：代码 — 提取提示词

```python
import json

def main(response: str) -> dict:
    data = json.loads(response)
    return {
        "gen_prompt": data.get("prompt", ""),
        "gen_negative": data.get("negative_prompt", ""),
    }
```

---

### 分支 B：修改后重生成

#### 节点 B1：HTTP — 获取当前分镜数据

同 A1。

#### 节点 B1P：代码 — 合并新旧提示词

```python
import json

def main(response: str, new_prompt: str = "", new_negative_prompt: str = "", new_description: str = "") -> dict:
    data = json.loads(response)
    prompt = new_prompt if new_prompt else data.get("prompt", "")
    negative = new_negative_prompt if new_negative_prompt else data.get("negative_prompt", "")

    # 如果用户改了画面描述，需要 LLM 重新生成 prompt
    # 这里简化：直接用描述作为 prompt 的一部分
    if new_description and not new_prompt:
        prompt = f"{new_description}, detailed, cinematic"

    return {
        "gen_prompt": prompt,
        "gen_negative": negative,
    }
```

---

### 汇合：调用生图引擎

#### 节点 G1：HTTP — 调用生图

**POST** 引擎 URL
**Body**：
```json
{
  "prompt": "{{gen_prompt}}",
  "negative_prompt": "{{gen_negative}}",
  "width": 1024,
  "height": 576,
  "steps": 30,
  "seed": -1
}
```

#### 节点 G1P：代码 — 提取图片路径

```python
import json

def main(image_response: str) -> dict:
    data = json.loads(image_response)
    return {"new_image_path": data.get("image_url", "")}
```

#### 节点 G2：HTTP — 更新分镜图片

**POST** `http://localhost:5005/api/shots/{{shot_id}}/image`
**Body**：
```json
{
  "image_path": "{{new_image_path}}",
  "prompt": "{{gen_prompt}}"
}
```

---

### 节点 3：输出

**回复内容**：
```
图片已更新！
分镜 ID：{{shot_id}}
新图片：{{new_image_path}}
```
```

---