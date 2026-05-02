好，全部重写为手动搭建版。每个节点编号、类型、配置、连线关系都交代清楚。内容量大，分两批输出。

---

# 手动搭建版 — 第一批：Workflow-A + Workflow-B

---

## 通用说明

```
连线规则：
  "A → B" 表示节点 A 的输出连接到节点 B 的输入
  "A[true] → B" 表示 A 的 IF 分支连接到 B
  "A[false] → B" 表示 A 的 ELSE 分支连接到 B

变量引用规则：
  引用某个节点的输出变量：{{#节点名称.变量名#}}
  引用迭代内部的当前项：{{#item.字段名#}}

代码节点输入变量配置：
  每个代码节点的 variables 列表中，variable 是函数参数名，
  value_selector 是从哪个节点取哪个变量。
```

---

## Workflow-A：文本预处理

```
应用名称：文章转视频 - 文本预处理
应用类型：工作流编排
```

### 节点总览与连线

```
[开始] → [if-判断拆分模式]
              ├── true → [llm-自动拆分] → [code-解析自动结果] ──┐
              └── false → [code-手动切分] ──────────────────────┤
                                                                 ▼
                                                     [if-解析是否成功]
                                                      ├── true → [http-创建项目] → [code-提取项目ID] → [code-准备段落数组] → [iter-遍历段落]
                                                      │                                                                                      │
                                                      │                                                                                      ├── 循环体内：[llm-生成分镜] → [code-解析分镜] → [http-保存段落]
                                                      │                                                                                      │
                                                      │                                                                                      └── 循环结束 → [end-完成]
                                                      │
                                                      └── false → [end-错误提示]
```

### 节点 1：开始

```
节点名称：开始
节点类型：开始

输入变量配置：
  变量 1：
    变量名：input_text
    类型：段落（Paragraph）
    必填：是
    标签：输入文本

  变量 2：
    变量名：split_mode
    类型：单选（Select）
    必填：是
    标签：拆分模式
    选项：
      · 自动拆分 → auto
      · 手动拆分 → manual

  变量 3：
    变量名：project_name
    类型：文本（Text Input）
    必填：否
    标签：项目名称
    默认值：未命名项目

  变量 4：
    变量名：style_hint
    类型：文本（Text Input）
    必填：否
    标签：画风偏好
    默认值：（留空）

输出连线：→ 节点 2
```

### 节点 2：判断拆分模式

```
节点名称：if-判断拆分模式
节点类型：条件分支（IF/ELSE）

条件配置：
  条件 1：
    变量：{{#开始.split_mode#}}
    操作符：等于（==）
    值：auto

输出连线：
  IF（true）→ 节点 3A
  ELSE（false）→ 节点 3B
```

### 节点 3A：LLM 自动拆分

```
节点名称：llm-自动拆分
节点类型：LLM

模型配置：
  模型：选择你已配置的 LLM（如 deepseek-chat）
  温度：0.3
  最大 Token：8192

系统提示词：
  你是一个专业的文章结构分析师。你的任务是将长文按自然段落或场景切分。

  切分原则：
  1. 每段包含一个完整场景或情节片段
  2. 每段 200-800 字，太长继续拆
  3. 在场景切换、时间跳跃、地点变化处切分
  4. 保持对话完整性
  5. 如有明确章节标记，优先按章节切分

用户提示词：
  请将以下文章切分为段落，严格按 JSON 格式输出，不要输出任何其他内容：

  {"segments": [{"index": 1, "title": "段落标题", "content": "段落正文", "summary": "一句话概括"}]}

  文章内容：
  {{#开始.input_text#}}

输出变量名：text（LLM 节点默认输出变量名为 text）

输出连线：→ 节点 4A
```

### 节点 4A：解析自动拆分结果

```
节点名称：code-解析自动结果
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：auto_split_result
    值来源：{{#llm-自动拆分.text#}}

Python 代码：
  import json
  import re

  def main(auto_split_result: str) -> dict:
      try:
          json_match = re.search(r'\{[\s\S]*\}', auto_split_result)
          if json_match:
              data = json.loads(json_match.group())
          else:
              data = json.loads(auto_split_result)

          segments = data.get("segments", [])
          if not segments:
              return {"segments_json": "[]", "parse_success": "false", "segment_count": "0"}

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
      except Exception:
          return {"segments_json": "[]", "parse_success": "false", "segment_count": "0"}

输出变量：segments_json, parse_success, segment_count

输出连线：→ 节点 5
```

### 节点 3B：手动标记切分

```
节点名称：code-手动切分
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：input_text
    值来源：{{#开始.input_text#}}

Python 代码：
  import re
  import json

  def main(input_text: str) -> dict:
      pattern = r'===\[([^\]]*)\]===|===SPLIT==='
      parts = re.split(pattern, input_text)
      segments = []
      index = 1
      i = 0
      current_title = ""

      while i < len(parts):
          if parts[i] is None:
              i += 1
              continue
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

      return {
          "segments_json": json.dumps(segments, ensure_ascii=False),
          "parse_success": "true" if segments else "false",
          "segment_count": str(len(segments)),
      }

输出变量：segments_json, parse_success, segment_count

输出连线：→ 节点 5

注意：节点 3B 和节点 4A 的输出变量名相同，它们都连接到节点 5。
Dify 会自动处理，节点 5 读取的是实际执行分支的输出。
```

### 节点 5：解析是否成功

```
节点名称：if-解析是否成功
节点类型：条件分支（IF/ELSE）

条件配置：
  条件 1：
    变量：{{#code-解析自动结果.parse_success#}}
    操作符：等于（==）
    值：true

  注意：如果走的是手动拆分分支，变量引用改为 {{#code-手动切分.parse_success#}}
  Dify 中需要根据实际分支设置。如果两个分支都连到同一个条件节点，
  可能需要在条件节点中同时配置两个变量的 OR 条件，或者用代码节点先汇合。

  推荐方案：在条件节点前加一个代码节点做汇合：

  新增节点 4M（代码-汇合结果）：
    输入变量：
      · parse_success_1 = {{#code-解析自动结果.parse_success#}}
      · parse_success_2 = {{#code-手动切分.parse_success#}}
      · segments_json_1 = {{#code-解析自动结果.segments_json#}}
      · segments_json_2 = {{#code-手动切分.segments_json#}}
      · segment_count_1 = {{#code-解析自动结果.segment_count#}}
      · segment_count_2 = {{#code-手动切分.segment_count#}}

    代码：
      def main(parse_success_1: str = "false", parse_success_2: str = "false",
               segments_json_1: str = "[]", segments_json_2: str = "[]",
               segment_count_1: str = "0", segment_count_2: str = "0") -> dict:
          if parse_success_1 == "true":
              return {"segments_json": segments_json_1, "parse_success": "true", "segment_count": segment_count_1}
          if parse_success_2 == "true":
              return {"segments_json": segments_json_2, "parse_success": "true", "segment_count": segment_count_2}
          return {"segments_json": "[]", "parse_success": "false", "segment_count": "0"}

    输出变量：segments_json, parse_success, segment_count

  连线调整：
    节点 4A → 节点 4M
    节点 3B → 节点 4M
    节点 4M → 节点 5

  节点 5 的条件变量改为：{{#code-汇合结果.parse_success#}}

输出连线：
  IF（true）→ 节点 6
  ELSE（false）→ 节点 5E
```

### 节点 5E：错误提示

```
节点名称：end-错误提示
节点类型：结束

输出配置：
  变量：result
  值：文本解析失败。请检查：自动模式确保文本大于100字，手动模式确保使用 ===SPLIT=== 标记。

无输出连线。
```

### 节点 6：创建项目

```
节点名称：http-创建项目
节点类型：HTTP 请求

配置：
  方法：POST
  URL：http://localhost:5005/api/projects
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "name": "{{#开始.project_name#}}",
      "source_text": "{{#开始.input_text#}}",
      "split_mode": "{{#开始.split_mode#}}",
      "style_hint": "{{#开始.style_hint#}}"
    }
  超时：读取 30 秒

输出变量名：body（HTTP 节点默认输出变量名）

输出连线：→ 节点 7
```

### 节点 7：提取项目 ID

```
节点名称：code-提取项目ID
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：project_response
    值来源：{{#http-创建项目.body#}}

Python 代码：
  import json

  def main(project_response: str) -> dict:
      try:
          data = json.loads(project_response)
          return {"project_id": data.get("id", "")}
      except Exception:
          return {"project_id": ""}

输出变量：project_id

输出连线：→ 节点 8
```

### 节点 8：准备段落数组

```
节点名称：code-准备段落数组
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：segments_json
    值来源：{{#code-汇合结果.segments_json#}}

Python 代码：
  import json

  def main(segments_json: str) -> dict:
      segments = json.loads(segments_json)
      return {"segment_list": segments}

输出变量：segment_list

输出连线：→ 节点 9
```

### 节点 9：循环遍历段落

```
节点名称：iter-遍历段落
节点类型：迭代（Iteration）

配置：
  输入数组：{{#code-准备段落数组.segment_list#}}

循环体内连线：
  [llm-生成分镜] → [code-解析分镜] → [http-保存段落]

循环结束后连线：→ 节点 12（结束）
```

### 节点 10：循环体内 — LLM 生成分镜

```
节点名称：llm-生成分镜
节点类型：LLM
位置：迭代节点内部

模型配置：
  模型：选择你已配置的 LLM
  温度：0.5
  最大 Token：4096

系统提示词：
  你是一个专业的分镜脚本编剧。你将把一段文字转化为可视化的分镜脚本。
  每个分镜代表一个画面，包含画面描述、生图提示词、台词或旁白、镜头指示。

用户提示词：
  请将以下段落转化为分镜脚本。每个分镜代表一个画面。一段文字通常拆分为 3-8 个分镜。

  段落标题：{{#item.title#}}
  段落内容：{{#item.content#}}

  严格按 JSON 格式输出，不要输出任何其他内容：
  {"shots": [{"shot_index": 1, "scene_description": "画面场景的中文描述", "prompt": "English prompt for image generation, detailed, including character appearance, scene, lighting, mood", "negative_prompt": "blurry, low quality, distorted, deformed", "dialogue": "角色台词", "narrator_text": "旁白文字", "speaker": "说话人姓名", "camera": "近景/中景/远景/特写", "characters": ["出场人物"], "duration_hint": 5}]}

输出连线：→ 节点 11
```

### 节点 11：循环体内 — 解析分镜

```
节点名称：code-解析分镜
节点类型：代码执行
位置：迭代节点内部

输入变量配置：
  变量 1：
    变量名：shot_result
    值来源：{{#llm-生成分镜.text#}}

Python 代码：
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
          return {"shots_json": json.dumps(shots, ensure_ascii=False), "shot_count": str(len(shots))}
      except Exception:
          return {"shots_json": "[]", "shot_count": "0"}

输出变量：shots_json, shot_count

输出连线：→ 节点 11S
```

### 节点 11S：循环体内 — 保存段落分镜

```
节点名称：http-保存段落
节点类型：HTTP 请求
位置：迭代节点内部

配置：
  方法：POST
  URL：http://localhost:5005/api/projects/{{#code-提取项目ID.project_id#}}/segments
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "segment_index": {{#item.index#}},
      "title": "{{#item.title#}}",
      "content": "{{#item.content#}}",
      "summary": "{{#item.summary#}}",
      "shots": {{#code-解析分镜.shots_json#}}
    }
  超时：读取 30 秒

无后续连线（迭代体内最后一个节点）。
```

### 节点 12：完成

```
节点名称：end-完成
节点类型：结束

输出配置：
  变量：result
  值：文本预处理完成！项目已创建，段落和分镜已保存。

无输出连线。
```

---

## Workflow-B：单段渲染

```
应用名称：文章转视频 - 单段渲染
应用类型：工作流编排
```

### 节点总览与连线

```
[开始] → [http-获取段落] → [code-解析分镜列表] → [iter-遍历分镜]
                                                              │
                                                              ├── 循环体内：
                                                              │   [code-构造提示词] → [http-调用生图] → [code-提取图片] → [http-保存图片]
                                                              │       → [if-有台词] → [http-调用TTS] → [code-提取音频] → [http-保存音频]
                                                              │
                                                              └── 循环结束 → [http-更新段落状态] → [end-完成]
```

### 节点 1：开始

```
节点名称：开始
节点类型：开始

输入变量配置：
  变量 1：
    变量名：segment_id
    类型：文本（Text Input）
    必填：是
    标签：段落ID

  变量 2：
    变量名：project_id
    类型：文本（Text Input）
    必填：是
    标签：项目ID

  变量 3：
    变量名：style_hint
    类型：文本（Text Input）
    必填：否
    标签：画风偏好
    默认值：（留空）

输出连线：→ 节点 2
```

### 节点 2：获取段落数据

```
节点名称：http-获取段落
节点类型：HTTP 请求

配置：
  方法：GET
  URL：http://localhost:5005/api/segments/{{#开始.segment_id#}}
  Headers：Content-Type: application/json
  超时：读取 30 秒

输出变量名：body

输出连线：→ 节点 3
```

### 节点 3：解析分镜列表

```
节点名称：code-解析分镜列表
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：segment_response
    值来源：{{#http-获取段落.body#}}

Python 代码：
  import json

  def main(segment_response: str) -> dict:
      data = json.loads(segment_response)
      shots = data.get("shots", [])
      title = data.get("title", "")
      return {"shots_list": shots, "segment_title": title, "shot_count": str(len(shots))}

输出变量：shots_list, segment_title, shot_count

输出连线：→ 节点 4
```

### 节点 4：循环遍历分镜

```
节点名称：iter-遍历分镜
节点类型：迭代（Iteration）

配置：
  输入数组：{{#code-解析分镜列表.shots_list#}}

循环体内连线：
  [code-构造提示词] → [http-调用生图] → [code-提取图片] → [http-保存图片] → [if-有台词]
                                                                                   ├── true → [http-调用TTS] → [code-提取音频] → [http-保存音频]
                                                                                   └── false → （跳过，进入下一个迭代）

循环结束后连线：→ 节点 5（http-更新段落状态）
```

### 节点 4.1：循环体内 — 构造提示词

```
节点名称：code-构造提示词
节点类型：代码执行
位置：迭代节点内部

输入变量配置：
  变量 1：
    变量名：item
    值来源：{{#item#}}（迭代当前项）

  变量 2：
    变量名：style_hint
    值来源：{{#开始.style_hint#}}

  注意：Dify 迭代节点内部引用外部变量可能有限制。
  如果无法引用，可以在开始节点的输入中直接写死画风偏好，
  或者在迭代前用代码节点把 style_hint 注入到每个 shot 对象中。

Python 代码：
  def main(item: dict, style_hint: str = "") -> dict:
      prompt = item.get("prompt", "")
      if style_hint:
          prompt = f"{prompt}, {style_hint}"
      dialogue = item.get("dialogue", "")
      narrator_text = item.get("narrator_text", "")
      tts_text = dialogue if dialogue else narrator_text
      has_text = "true" if tts_text else "false"
      return {
          "final_prompt": prompt,
          "final_negative": item.get("negative_prompt", "blurry, low quality"),
          "shot_id": item.get("id", ""),
          "has_text": has_text,
          "tts_text": tts_text,
          "tts_speaker": item.get("speaker", ""),
      }

输出变量：final_prompt, final_negative, shot_id, has_text, tts_text, tts_speaker

输出连线：→ 节点 4.2
```

### 节点 4.2：循环体内 — 调用生图引擎

```
节点名称：http-调用生图
节点类型：HTTP 请求
位置：迭代节点内部

配置：
  方法：POST
  URL：http://localhost:8188/api/prompt

  注意：URL 改为你的实际生图引擎地址。
  如果是 SD WebUI，URL 为 http://localhost:7860/sdapi/v1/txt2img
  Body 格式也需要根据引擎调整。

  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "prompt": "{{#code-构造提示词.final_prompt#}}",
      "negative_prompt": "{{#code-构造提示词.final_negative#}}",
      "width": 1024,
      "height": 576,
      "steps": 30,
      "seed": -1
    }
  超时：读取 120 秒

输出变量名：body

输出连线：→ 节点 4.3
```

### 节点 4.3：循环体内 — 提取图片路径

```
节点名称：code-提取图片
节点类型：代码执行
位置：迭代节点内部

输入变量配置：
  变量 1：
    变量名：image_response
    值来源：{{#http-调用生图.body#}}

Python 代码：
  import json

  def main(image_response: str) -> dict:
      try:
          data = json.loads(image_response)
          # 适配不同引擎返回格式，按需修改
          image_url = data.get("image_url", "")
          if not image_url:
              # 尝试 ComfyUI 格式
              images = data.get("output", {}).get("images", []) if isinstance(data.get("output"), dict) else []
              if images:
                  image_url = images[0]
          if not image_url:
              # 尝试 SD WebUI 格式
              images = data.get("images", [])
              if images:
                  image_url = images[0]
          return {"image_path": image_url}
      except Exception:
          return {"image_path": ""}

输出变量：image_path

输出连线：→ 节点 4.4
```

### 节点 4.4：循环体内 — 保存图片

```
节点名称：http-保存图片
节点类型：HTTP 请求
位置：迭代节点内部

配置：
  方法：POST
  URL：http://localhost:5005/api/shots/{{#code-构造提示词.shot_id#}}/image
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "image_path": "{{#code-提取图片.image_path#}}"
    }
  超时：读取 30 秒

输出连线：→ 节点 4.5
```

### 节点 4.5：循环体内 — 是否有台词

```
节点名称：if-有台词
节点类型：条件分支（IF/ELSE）
位置：迭代节点内部

条件配置：
  条件 1：
    变量：{{#code-构造提示词.has_text#}}
    操作符：等于（==）
    值：true

输出连线：
  IF（true）→ 节点 4.6
  ELSE（false）→ 不连接（跳过 TTS，进入下一个迭代）
```

### 节点 4.6：循环体内 — 调用 TTS

```
节点名称：http-调用TTS
节点类型：HTTP 请求
位置：迭代节点内部

配置：
  方法：POST
  URL：http://localhost:8004/tts

  注意：URL 改为你的实际 TTS 引擎地址。
  Body 格式根据引擎调整。

  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "text": "{{#code-构造提示词.tts_text#}}",
      "speaker": "{{#code-构造提示词.tts_speaker#}}",
      "speed": 1.0
    }
  超时：读取 30 秒

输出变量名：body

输出连线：→ 节点 4.7
```

### 节点 4.7：循环体内 — 提取音频

```
节点名称：code-提取音频
节点类型：代码执行
位置：迭代节点内部

输入变量配置：
  变量 1：
    变量名：tts_response
    值来源：{{#http-调用TTS.body#}}

Python 代码：
  import json

  def main(tts_response: str) -> dict:
      try:
          data = json.loads(tts_response)
          return {
              "audio_path": data.get("audio_url", ""),
              "audio_duration": str(data.get("duration", 5.0)),
          }
      except Exception:
          return {"audio_path": "", "audio_duration": "5.0"}

输出变量：audio_path, audio_duration

输出连线：→ 节点 4.8
```

### 节点 4.8：循环体内 — 保存音频

```
节点名称：http-保存音频
节点类型：HTTP 请求
位置：迭代节点内部

配置：
  方法：POST
  URL：http://localhost:5005/api/shots/{{#code-构造提示词.shot_id#}}/audio
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "audio_path": "{{#code-提取音频.audio_path#}}",
      "duration": {{#code-提取音频.audio_duration#}}
    }
  超时：读取 30 秒

无后续连线（迭代体内最后一个节点）。
```

### 节点 5：更新段落状态

```
节点名称：http-更新段落状态
节点类型：HTTP 请求

配置：
  方法：PUT
  URL：http://localhost:5005/api/segments/{{#开始.segment_id#}}
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "status": "rendered"
    }
  超时：读取 30 秒

输出连线：→ 节点 6
```

### 节点 6：完成

```
节点名称：end-完成
节点类型：结束

输出配置：
  变量：result
  值：段落渲染完成！

无输出连线。
```

---

## 搭建检查清单

```
Workflow-A 搭建完成后检查：
  □ 开始节点有 4 个输入变量
  □ 条件分支 split_mode == auto 正确分流
  □ LLM 节点的模型已选择
  □ 代码节点的输入变量引用正确
  □ 汇合代码节点正确合并两个分支的输出
  □ HTTP 节点的 URL 正确
  □ 迭代节点的输入是数组类型
  □ 迭代内部 3 个节点连线正确
  □ 结束节点有输出

Workflow-B 搭建完成后检查：
  □ 开始节点有 3 个输入变量
  □ HTTP 获取段落的 URL 包含 segment_id
  □ 代码节点正确解析 shots 数组
  □ 迭代节点输入是数组
  □ 迭代内部 8 个节点连线正确
  □ 条件分支 has_text == true 正确分流
  □ 生图引擎 URL 正确
  □ TTS 引擎 URL 正确
  □ 保存图片/音频的 API URL 包含 shot_id
  □ 循环结束后更新段落状态
```

---

第一批完成（Workflow-A + Workflow-B）。确认无误后我输出第二批（Workflow-C + Workflow-D + Workflow-E + 快速模式）。