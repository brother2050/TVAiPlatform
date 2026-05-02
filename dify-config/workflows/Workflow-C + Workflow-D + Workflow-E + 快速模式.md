# 手动搭建版 — 第二批：Workflow-C + Workflow-D + Workflow-E + 快速模式

---

## Workflow-C：图片审核重生成

```
应用名称：文章转视频 - 图片审核重生成
应用类型：工作流编排
```

### 节点总览与连线

```
[开始] → [if-判断操作类型]
              ├── true（regenerate）→ [http-获取分镜A] → [code-提取原始提示词] → [http-生图A] → [code-提取图片A] → [http-保存图片A] ──┐
              └── false（edit）     → [http-获取分镜B] → [code-合并新旧提示词] → [http-生图B] → [code-提取图片B] → [http-保存图片B] ──┤
                                                                                                                                         ▼
                                                                                                                               [end-图片已更新]
```

### 节点 1：开始

```
节点名称：开始
节点类型：开始

输入变量配置：
  变量 1：
    变量名：shot_id
    类型：文本（Text Input）
    必填：是
    标签：分镜ID

  变量 2：
    变量名：action
    类型：单选（Select）
    必填：是
    标签：操作类型
    选项：
      · 原词重生成 → regenerate
      · 修改后重生成 → edit_and_regenerate

  变量 3：
    变量名：new_prompt
    类型：文本（Text Input）
    必填：否
    标签：修改后的提示词
    默认值：（留空）

  变量 4：
    变量名：new_negative
    类型：文本（Text Input）
    必填：否
    标签：修改后的负面提示词
    默认值：（留空）

  变量 5：
    变量名：new_description
    类型：文本（Text Input）
    必填：否
    标签：修改后的画面描述
    默认值：（留空）

输出连线：→ 节点 2
```

### 节点 2：判断操作类型

```
节点名称：if-判断操作类型
节点类型：条件分支（IF/ELSE）

条件配置：
  条件 1：
    变量：{{#开始.action#}}
    操作符：等于（==）
    值：regenerate

输出连线：
  IF（true）→ 节点 3A
  ELSE（false）→ 节点 3B
```

### 节点 3A：获取分镜（原词分支）

```
节点名称：http-获取分镜A
节点类型：HTTP 请求

配置：
  方法：GET
  URL：http://localhost:5005/api/shots/{{#开始.shot_id#}}
  Headers：Content-Type: application/json
  超时：读取 30 秒

输出变量名：body

输出连线：→ 节点 4A
```

### 节点 4A：提取原始提示词

```
节点名称：code-提取原始提示词
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：response
    值来源：{{#http-获取分镜A.body#}}

Python 代码：
  import json

  def main(response: str) -> dict:
      data = json.loads(response)
      return {
          "gen_prompt": data.get("prompt", ""),
          "gen_negative": data.get("negative_prompt", "blurry, low quality"),
      }

输出变量：gen_prompt, gen_negative

输出连线：→ 节点 5A
```

### 节点 5A：调用生图引擎（原词）

```
节点名称：http-生图A
节点类型：HTTP 请求

配置：
  方法：POST
  URL：http://localhost:8188/api/prompt

  注意：改为你的实际生图引擎地址。

  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "prompt": "{{#code-提取原始提示词.gen_prompt#}}",
      "negative_prompt": "{{#code-提取原始提示词.gen_negative#}}",
      "width": 1024,
      "height": 576,
      "steps": 30,
      "seed": -1
    }
  超时：读取 120 秒

输出变量名：body

输出连线：→ 节点 6A
```

### 节点 6A：提取图片路径（原词）

```
节点名称：code-提取图片A
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：image_response
    值来源：{{#http-生图A.body#}}

Python 代码：
  import json

  def main(image_response: str) -> dict:
      try:
          data = json.loads(image_response)
          return {"new_image_path": data.get("image_url", "")}
      except Exception:
          return {"new_image_path": ""}

输出变量：new_image_path

输出连线：→ 节点 7A
```

### 节点 7A：保存图片（原词）

```
节点名称：http-保存图片A
节点类型：HTTP 请求

配置：
  方法：POST
  URL：http://localhost:5005/api/shots/{{#开始.shot_id#}}/image
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "image_path": "{{#code-提取图片A.new_image_path#}}"
    }
  超时：读取 30 秒

输出连线：→ 节点 8（end-图片已更新）
```

### 节点 3B：获取分镜（编辑分支）

```
节点名称：http-获取分镜B
节点类型：HTTP 请求

配置：
  方法：GET
  URL：http://localhost:5005/api/shots/{{#开始.shot_id#}}
  Headers：Content-Type: application/json
  超时：读取 30 秒

输出变量名：body

输出连线：→ 节点 4B
```

### 节点 4B：合并新旧提示词

```
节点名称：code-合并新旧提示词
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：response
    值来源：{{#http-获取分镜B.body#}}

  变量 2：
    变量名：new_prompt
    值来源：{{#开始.new_prompt#}}

  变量 3：
    变量名：new_negative
    值来源：{{#开始.new_negative#}}

  变量 4：
    变量名：new_description
    值来源：{{#开始.new_description#}}

Python 代码：
  import json

  def main(response: str, new_prompt: str = "", new_negative: str = "", new_description: str = "") -> dict:
      data = json.loads(response)
      prompt = new_prompt if new_prompt else data.get("prompt", "")
      negative = new_negative if new_negative else data.get("negative_prompt", "blurry, low quality")
      if new_description and not new_prompt:
          prompt = f"{new_description}, detailed, cinematic"
      return {"gen_prompt": prompt, "gen_negative": negative}

输出变量：gen_prompt, gen_negative

输出连线：→ 节点 5B
```

### 节点 5B：调用生图引擎（编辑）

```
节点名称：http-生图B
节点类型：HTTP 请求

配置：
  方法：POST
  URL：http://localhost:8188/api/prompt

  注意：改为你的实际生图引擎地址。

  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "prompt": "{{#code-合并新旧提示词.gen_prompt#}}",
      "negative_prompt": "{{#code-合并新旧提示词.gen_negative#}}",
      "width": 1024,
      "height": 576,
      "steps": 30,
      "seed": -1
    }
  超时：读取 120 秒

输出变量名：body

输出连线：→ 节点 6B
```

### 节点 6B：提取图片路径（编辑）

```
节点名称：code-提取图片B
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：image_response
    值来源：{{#http-生图B.body#}}

Python 代码：
  import json

  def main(image_response: str) -> dict:
      try:
          data = json.loads(image_response)
          return {"new_image_path": data.get("image_url", "")}
      except Exception:
          return {"new_image_path": ""}

输出变量：new_image_path

输出连线：→ 节点 7B
```

### 节点 7B：保存图片（编辑）

```
节点名称：http-保存图片B
节点类型：HTTP 请求

配置：
  方法：POST
  URL：http://localhost:5005/api/shots/{{#开始.shot_id#}}/image
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "image_path": "{{#code-提取图片B.new_image_path#}}",
      "prompt": "{{#code-合并新旧提示词.gen_prompt#}}"
    }
  超时：读取 30 秒

  注意：编辑分支会同时更新 prompt 字段，原词分支不更新。

输出连线：→ 节点 8（end-图片已更新）
```

### 节点 8：完成

```
节点名称：end-图片已更新
节点类型：结束

输出配置：
  变量：result
  值：图片已更新，请在项目管理中查看。

无输出连线。
```

---

## Workflow-D：确认并合成

```
应用名称：文章转视频 - 确认并合成
应用类型：工作流编排
```

### 节点总览与连线

```
[开始] → [http-确认分镜] → [http-获取已确认分镜] → [code-构造合成请求] → [http-调用合成] → [code-提取结果] → [http-更新段落] → [end-完成]
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
    变量名：output_format
    类型：单选（Select）
    必填：否
    标签：输出格式
    选项：
      · 横屏16:9 → horizontal_16_9
      · 竖屏9:16 → vertical_9_16
      · 方形1:1 → square_1_1
    默认值：horizontal_16_9

  变量 3：
    变量名：title_text
    类型：文本（Text Input）
    必填：否
    标签：片头文字
    默认值：（留空）

输出连线：→ 节点 2
```

### 节点 2：确认所有分镜

```
节点名称：http-确认分镜
节点类型：HTTP 请求

配置：
  方法：PUT
  URL：http://localhost:5005/api/segments/{{#开始.segment_id#}}/confirm
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {}
  超时：读取 30 秒

输出连线：→ 节点 3
```

### 节点 3：获取已确认分镜

```
节点名称：http-获取已确认分镜
节点类型：HTTP 请求

配置：
  方法：GET
  URL：http://localhost:5005/api/segments/{{#开始.segment_id#}}/shots?status=confirmed
  Headers：Content-Type: application/json
  超时：读取 30 秒

输出变量名：body

输出连线：→ 节点 4
```

### 节点 4：构造合成请求

```
节点名称：code-构造合成请求
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：confirmed_response
    值来源：{{#http-获取已确认分镜.body#}}

  变量 2：
    变量名：segment_id
    值来源：{{#开始.segment_id#}}

  变量 3：
    变量名：output_format
    值来源：{{#开始.output_format#}}

  变量 4：
    变量名：title_text
    值来源：{{#开始.title_text#}}

Python 代码：
  import json

  def main(confirmed_response: str, segment_id: str, output_format: str = "horizontal_16_9", title_text: str = "") -> dict:
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
          "subtitle": {"enabled": True, "font_size": 24},
          "transition": {"type": "fade", "duration": 0.5},
          "title": title_config,
      }
      return {"compose_body": json.dumps(request_body, ensure_ascii=False)}

输出变量：compose_body

输出连线：→ 节点 5
```

### 节点 5：调用视频合成

```
节点名称：http-调用合成
节点类型：HTTP 请求

配置：
  方法：POST
  URL：http://localhost:5003/api/compositor/segment
  Headers：Content-Type: application/json
  Body 类型：JSON（选择"自定义"或"raw"）
  Body 内容：
    {{#code-构造合成请求.compose_body#}}

  注意：Body 直接引用 compose_body 变量，因为它已经是完整的 JSON 字符串。
  如果 Dify 要求 Body 为对象格式，需要把 compose_body 解析后再填入。
  最简单的方式是在 Body 中选择"文本"模式，直接填变量。

  超时：读取 300 秒（5分钟，视频合成耗时较长）

输出变量名：body

输出连线：→ 节点 6
```

### 节点 6：提取合成结果

```
节点名称：code-提取结果
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：compose_response
    值来源：{{#http-调用合成.body#}}

Python 代码：
  import json

  def main(compose_response: str) -> dict:
      data = json.loads(compose_response)
      return {
          "video_path": data.get("video_path", ""),
          "video_duration": str(data.get("duration", 0)),
          "file_size": str(data.get("file_size_mb", 0)),
      }

输出变量：video_path, video_duration, file_size

输出连线：→ 节点 7
```

### 节点 7：更新段落状态

```
节点名称：http-更新段落
节点类型：HTTP 请求

配置：
  方法：PUT
  URL：http://localhost:5005/api/segments/{{#开始.segment_id#}}
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "status": "completed",
      "video_path": "{{#code-提取结果.video_path#}}",
      "video_duration": {{#code-提取结果.video_duration#}}
    }
  超时：读取 30 秒

输出连线：→ 节点 8
```

### 节点 8：完成

```
节点名称：end-完成
节点类型：结束

输出配置：
  变量 1：video_path = {{#code-提取结果.video_path#}}
  变量 2：video_duration = {{#code-提取结果.video_duration#}}
  变量 3：file_size_mb = {{#code-提取结果.file_size#}}

无输出连线。
```

---

## Workflow-E：合成输出（独立合成）

```
应用名称：文章转视频 - 合成输出
应用类型：工作流编排

说明：与 Workflow-D 几乎相同，区别在于开始节点多了转场和字幕参数。
     适用于调整合成参数后重新合成的场景。
```

### 节点总览与连线

```
[开始] → [http-获取已确认分镜] → [code-构造合成请求] → [http-调用合成] → [code-提取结果] → [http-更新段落] → [end-完成]

注意：Workflow-E 不包含"确认分镜"步骤（因为分镜已经在之前确认过了）。
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
    变量名：output_format
    类型：单选（Select）
    必填：否
    标签：输出格式
    选项：
      · 横屏16:9 → horizontal_16_9
      · 竖屏9:16 → vertical_9_16
    默认值：horizontal_16_9

  变量 3：
    变量名：transition_type
    类型：文本（Text Input）
    必填：否
    标签：转场类型
    默认值：fade

  变量 4：
    变量名：transition_duration
    类型：数字（Number）
    必填：否
    标签：转场时长（秒）
    默认值：0.5

  变量 5：
    变量名：title_text
    类型：文本（Text Input）
    必填：否
    标签：片头文字
    默认值：（留空）

  变量 6：
    变量名：subtitle_enabled
    类型：单选（Select）
    必填：否
    标签：启用字幕
    选项：
      · 是 → true
      · 否 → false
    默认值：true

输出连线：→ 节点 2
```

### 节点 2：获取已确认分镜

```
节点名称：http-获取已确认分镜
节点类型：HTTP 请求

配置：
  方法：GET
  URL：http://localhost:5005/api/segments/{{#开始.segment_id#}}/shots?status=confirmed
  Headers：Content-Type: application/json
  超时：读取 30 秒

输出变量名：body

输出连线：→ 节点 3
```

### 节点 3：构造合成请求

```
节点名称：code-构造合成请求
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：confirmed_response
    值来源：{{#http-获取已确认分镜.body#}}

  变量 2：
    变量名：segment_id
    值来源：{{#开始.segment_id#}}

  变量 3：
    变量名：output_format
    值来源：{{#开始.output_format#}}

  变量 4：
    变量名：transition_type
    值来源：{{#开始.transition_type#}}

  变量 5：
    变量名：transition_duration
    值来源：{{#开始.transition_duration#}}

  变量 6：
    变量名：title_text
    值来源：{{#开始.title_text#}}

  变量 7：
    变量名：subtitle_enabled
    值来源：{{#开始.subtitle_enabled#}}

Python 代码：
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

输出变量：compose_body

输出连线：→ 节点 4
```

### 节点 4：调用视频合成

```
节点名称：http-调用合成
节点类型：HTTP 请求

配置：
  方法：POST
  URL：http://localhost:5003/api/compositor/segment
  Headers：Content-Type: application/json
  Body 内容：{{#code-构造合成请求.compose_body#}}
  超时：读取 300 秒

输出变量名：body

输出连线：→ 节点 5
```

### 节点 5：提取结果

```
节点名称：code-提取结果
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：compose_response
    值来源：{{#http-调用合成.body#}}

Python 代码：
  import json

  def main(compose_response: str) -> dict:
      data = json.loads(compose_response)
      return {
          "video_path": data.get("video_path", ""),
          "video_duration": str(data.get("duration", 0)),
          "file_size": str(data.get("file_size_mb", 0)),
      }

输出变量：video_path, video_duration, file_size

输出连线：→ 节点 6
```

### 节点 6：更新段落状态

```
节点名称：http-更新段落
节点类型：HTTP 请求

配置：
  方法：PUT
  URL：http://localhost:5005/api/segments/{{#开始.segment_id#}}
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "status": "completed",
      "video_path": "{{#code-提取结果.video_path#}}",
      "video_duration": {{#code-提取结果.video_duration#}},
      "pending_recompose": false
    }
  超时：读取 30 秒

输出连线：→ 节点 7
```

### 节点 7：完成

```
节点名称：end-完成
节点类型：结束

输出配置：
  变量 1：video_path = {{#code-提取结果.video_path#}}
  变量 2：video_duration = {{#code-提取结果.video_duration#}}
  变量 3：file_size_mb = {{#code-提取结果.file_size#}}

无输出连线。
```

---

## 快速模式

```
应用名称：文章转视频 - 快速模式
应用类型：工作流编排
```

### 节点总览与连线

```
[开始] → [if-需要扩写]
              ├── true → [llm-大纲扩写] ──┐
              └── false ──────────────────┤
                                           ▼
                                 [code-选择最终文本] → [llm-生成分镜] → [code-创建项目并保存] → [http-获取分镜] → [code-准备渲染列表] → [iter-渲染分镜]
                                                                                                                                                       │
                                                                                                                                                       ├── 循环体内：
                                                                                                                                                       │   [code-构造提示词] → [http-生图] → [code-提取图片] → [http-保存图片]
                                                                                                                                                       │       → [http-TTS] → [code-提取音频] → [http-保存音频]
                                                                                                                                                       │
                                                                                                                                                       └── 循环结束 → [http-自动确认] → [http-获取已确认分镜]
                                                                                                                                                               → [code-构造合成请求] → [http-合成视频] → [code-提取最终结果]
                                                                                                                                                               → [http-更新段落完成] → [end-完成]
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
    标签：输入文字

  变量 2：
    变量名：style_hint
    类型：文本（Text Input）
    必填：否
    标签：画风偏好
    默认值：cinematic, high quality, detailed

输出连线：→ 节点 2
```

### 节点 2：判断是否需要扩写

```
节点名称：if-需要扩写
节点类型：条件分支（IF/ELSE）

条件配置：
  条件 1：
    变量：{{#开始.input_text#}}
    操作符：长度小于（Length <）
    值：200

  注意：Dify 的条件分支可能不直接支持"长度小于"操作符。
  如果不支持，用以下替代方案：

  替代方案：在条件分支前加一个代码节点做判断：

  新增节点 2P（代码-判断文本长度）：
    输入变量：
      · input_text = {{#开始.input_text#}}
    代码：
      def main(input_text: str) -> dict:
          return {
              "text_length": str(len(input_text)),
              "is_short": "true" if len(input_text) < 200 else "false",
          }
    输出变量：text_length, is_short

  然后条件分支改为：
    变量：{{#代码-判断文本长度.is_short#}}
    操作符：等于（==）
    值：true

  连线调整：
    开始 → 代码-判断文本长度 → if-需要扩写

输出连线：
  IF（true）→ 节点 3
  ELSE（false）→ 节点 4
```

### 节点 3：LLM 大纲扩写

```
节点名称：llm-大纲扩写
节点类型：LLM

模型配置：
  模型：选择你已配置的 LLM
  温度：0.8（创意扩写需要较高温度）
  最大 Token：4096

系统提示词：
  你是一个网文编剧。请将以下简短大纲扩写为一个完整的短篇故事场景（300-800字）。
  要求：有具体的场景描写、人物动作、对话。

用户提示词：
  {{#开始.input_text#}}

输出变量名：text

输出连线：→ 节点 4
```

### 节点 4：选择最终文本

```
节点名称：code-选择最终文本
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：input_text
    值来源：{{#开始.input_text#}}

  变量 2：
    变量名：expanded_text
    值来源：{{#llm-大纲扩写.text#}}

  注意：如果走的是 false 分支（不扩写），expanded_text 为空字符串。
  Dify 中两个分支都连到同一个节点时，未执行的分支输出为空。

Python 代码：
  def main(input_text: str, expanded_text: str = "") -> dict:
      if len(input_text) < 200 and expanded_text:
          return {"final_text": expanded_text}
      return {"final_text": input_text}

输出变量：final_text

输出连线：→ 节点 5
```

### 节点 5：LLM 生成分镜脚本

```
节点名称：llm-生成分镜
节点类型：LLM

模型配置：
  模型：选择你已配置的 LLM
  温度：0.5
  最大 Token：4096

系统提示词：
  你是一个专业的分镜脚本编剧。将文字转化为 4-8 个分镜。

用户提示词：
  将以下文字转化为分镜脚本，严格 JSON 输出：
  {"shots": [{"shot_index": 1, "scene_description": "中文画面描述", "prompt": "English prompt for image generation, detailed", "negative_prompt": "blurry, low quality, distorted", "dialogue": "台词", "narrator_text": "旁白", "speaker": "说话人", "camera": "镜头", "characters": ["人物"], "duration_hint": 5}]}

  文字内容：
  {{#code-选择最终文本.final_text#}}

输出变量名：text

输出连线：→ 节点 6
```

### 节点 6：创建项目并保存

```
节点名称：code-创建项目并保存
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：shot_result
    值来源：{{#llm-生成分镜.text#}}

  变量 2：
    变量名：final_text
    值来源：{{#code-选择最终文本.final_text#}}

Python 代码：
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
      try:
          json_match = re.search(r'\{[\s\S]*\}', shot_result)
          data = json.loads(json_match.group()) if json_match else json.loads(shot_result)
          shots = data.get("shots", [])
      except Exception:
          return {"project_id": "", "segment_id": "", "shot_count": "0"}

      # 创建项目
      project = api_call("POST", "/api/projects", {
          "name": "快速模式项目",
          "source_text": final_text,
          "split_mode": "auto",
      })
      project_id = project.get("id", "")
      if not project_id:
          return {"project_id": "", "segment_id": "", "shot_count": "0"}

      # 保存段落和分镜
      result = api_call("POST", f"/api/projects/{project_id}/segments", {
          "segment_index": 1,
          "title": "快速生成",
          "content": final_text,
          "summary": final_text[:50],
          "shots": shots,
      })

      return {
          "project_id": project_id,
          "segment_id": result.get("segment_id", ""),
          "shot_count": str(len(shots)),
      }

输出变量：project_id, segment_id, shot_count

输出连线：→ 节点 7
```

### 节点 7：获取分镜列表

```
节点名称：http-获取分镜
节点类型：HTTP 请求

配置：
  方法：GET
  URL：http://localhost:5005/api/segments/{{#code-创建项目并保存.segment_id#}}
  Headers：Content-Type: application/json
  超时：读取 30 秒

输出变量名：body

输出连线：→ 节点 8
```

### 节点 8：准备渲染列表

```
节点名称：code-准备渲染列表
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：segment_response
    值来源：{{#http-获取分镜.body#}}

Python 代码：
  import json

  def main(segment_response: str) -> dict:
      data = json.loads(segment_response)
      return {"shots_list": data.get("shots", [])}

输出变量：shots_list

输出连线：→ 节点 9
```

### 节点 9：循环渲染分镜

```
节点名称：iter-渲染分镜
节点类型：迭代（Iteration）

配置：
  输入数组：{{#code-准备渲染列表.shots_list#}}

循环体内连线：
  [code-构造提示词] → [http-生图] → [code-提取图片] → [http-保存图片]
      → [http-TTS] → [code-提取音频] → [http-保存音频]

循环结束后连线：→ 节点 10
```

### 节点 9.1：循环体内 — 构造提示词

```
节点名称：code-构造提示词
节点类型：代码执行
位置：迭代节点内部

输入变量配置：
  变量 1：
    变量名：item
    值来源：{{#item#}}

  变量 2：
    变量名：style_hint
    值来源：{{#开始.style_hint#}}

Python 代码：
  def main(item: dict, style_hint: str = "") -> dict:
      prompt = item.get("prompt", "")
      if style_hint:
          prompt = f"{prompt}, {style_hint}"
      dialogue = item.get("dialogue", "")
      narrator_text = item.get("narrator_text", "")
      tts_text = dialogue if dialogue else narrator_text
      return {
          "final_prompt": prompt,
          "final_negative": item.get("negative_prompt", "blurry, low quality"),
          "shot_id": item.get("id", ""),
          "tts_text": tts_text,
          "tts_speaker": item.get("speaker", ""),
      }

输出变量：final_prompt, final_negative, shot_id, tts_text, tts_speaker

输出连线：→ 节点 9.2
```

### 节点 9.2：循环体内 — 调用生图

```
节点名称：http-生图
节点类型：HTTP 请求
位置：迭代节点内部

配置：
  方法：POST
  URL：http://localhost:8188/api/prompt
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

输出连线：→ 节点 9.3
```

### 节点 9.3：循环体内 — 提取图片

```
节点名称：code-提取图片
节点类型：代码执行
位置：迭代节点内部

输入变量配置：
  变量 1：
    变量名：image_response
    值来源：{{#http-生图.body#}}

Python 代码：
  import json

  def main(image_response: str) -> dict:
      try:
          data = json.loads(image_response)
          return {"image_path": data.get("image_url", "")}
      except Exception:
          return {"image_path": ""}

输出变量：image_path

输出连线：→ 节点 9.4
```

### 节点 9.4：循环体内 — 保存图片

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

输出连线：→ 节点 9.5
```

### 节点 9.5：循环体内 — 调用 TTS

```
节点名称：http-TTS
节点类型：HTTP 请求
位置：迭代节点内部

配置：
  方法：POST
  URL：http://localhost:8004/tts
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

输出连线：→ 节点 9.6
```

### 节点 9.6：循环体内 — 提取音频

```
节点名称：code-提取音频
节点类型：代码执行
位置：迭代节点内部

输入变量配置：
  变量 1：
    变量名：tts_response
    值来源：{{#http-TTS.body#}}

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

输出连线：→ 节点 9.7
```

### 节点 9.7：循环体内 — 保存音频

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

### 节点 10：自动确认分镜

```
节点名称：http-自动确认
节点类型：HTTP 请求

配置：
  方法：PUT
  URL：http://localhost:5005/api/segments/{{#code-创建项目并保存.segment_id#}}/confirm
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {}
  超时：读取 30 秒

输出连线：→ 节点 11
```

### 节点 11：获取已确认分镜

```
节点名称：http-获取已确认分镜
节点类型：HTTP 请求

配置：
  方法：GET
  URL：http://localhost:5005/api/segments/{{#code-创建项目并保存.segment_id#}}/shots?status=confirmed
  Headers：Content-Type: application/json
  超时：读取 30 秒

输出变量名：body

输出连线：→ 节点 12
```

### 节点 12：构造合成请求

```
节点名称：code-构造合成请求
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：confirmed_response
    值来源：{{#http-获取已确认分镜.body#}}

  变量 2：
    变量名：segment_id
    值来源：{{#code-创建项目并保存.segment_id#}}

Python 代码：
  import json

  def main(confirmed_response: str, segment_id: str) -> dict:
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
      request_body = {
          "segment_id": segment_id,
          "shots": compose_shots,
          "output_format": "horizontal_16_9",
          "subtitle": {"enabled": True, "font_size": 24},
          "transition": {"type": "fade", "duration": 0.5},
          "title": {"enabled": False},
      }
      return {"compose_body": json.dumps(request_body, ensure_ascii=False)}

输出变量：compose_body

输出连线：→ 节点 13
```

### 节点 13：合成视频

```
节点名称：http-合成视频
节点类型：HTTP 请求

配置：
  方法：POST
  URL：http://localhost:5003/api/compositor/segment
  Headers：Content-Type: application/json
  Body 内容：{{#code-构造合成请求.compose_body#}}
  超时：读取 300 秒

输出变量名：body

输出连线：→ 节点 14
```

### 节点 14：提取最终结果

```
节点名称：code-提取最终结果
节点类型：代码执行

输入变量配置：
  变量 1：
    变量名：compose_response
    值来源：{{#http-合成视频.body#}}

Python 代码：
  import json

  def main(compose_response: str) -> dict:
      data = json.loads(compose_response)
      return {
          "video_path": data.get("video_path", ""),
          "video_duration": str(data.get("duration", 0)),
          "file_size": str(data.get("file_size_mb", 0)),
      }

输出变量：video_path, video_duration, file_size

输出连线：→ 节点 15
```

### 节点 15：更新段落完成

```
节点名称：http-更新段落完成
节点类型：HTTP 请求

配置：
  方法：PUT
  URL：http://localhost:5005/api/segments/{{#code-创建项目并保存.segment_id#}}
  Headers：Content-Type: application/json
  Body 类型：JSON
  Body 内容：
    {
      "status": "completed",
      "video_path": "{{#code-提取最终结果.video_path#}}",
      "video_duration": {{#code-提取最终结果.video_duration#}}
    }
  超时：读取 30 秒

输出连线：→ 节点 16
```

### 节点 16：完成

```
节点名称：end-完成
节点类型：结束

输出配置：
  变量 1：message = 快速模式完成！视频已生成。
  变量 2：project_id = {{#code-创建项目并保存.project_id#}}
  变量 3：video_path = {{#code-提取最终结果.video_path#}}
  变量 4：video_duration = {{#code-提取最终结果.video_duration#}}
  变量 5：shot_count = {{#code-创建项目并保存.shot_count#}}

无输出连线。
```

---

## 六个工作流搭建总结

```
┌─────────────────────────────────────┬──────────┬──────────────────────────────────┐
│ 工作流                               │ 节点数   │ 核心链路                          │
├─────────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Workflow-A 文本预处理                 │ 12       │ 拆分 → LLM分镜 → 保存数据库       │
│ Workflow-B 单段渲染                   │ 12       │ 获取分镜 → 生图 → TTS → 保存      │
│ Workflow-C 图片审核重生成              │ 8        │ 原词/编辑两条分支 → 生图 → 保存    │
│ Workflow-D 确认并合成                  │ 8        │ 确认 → 获取产物 → 合成 → 更新      │
│ Workflow-E 合成输出                   │ 7        │ 获取产物 → 自定义参数 → 合成       │
│ 快速模式                              │ 16       │ 扩写 → 分镜 → 渲染 → 确认 → 合成  │
└─────────────────────────────────────┴──────────┴──────────────────────────────────┘

搭建顺序建议：
  1. 先搭 Workflow-A → 测试文本输入和分镜生成
  2. 再搭 Workflow-B → 测试单段渲染
  3. 搭 Workflow-D → 测试合成
  4. 搭 Workflow-C → 测试重生成
  5. 搭 Workflow-E → 测试独立合成
  6. 最后搭快速模式 → 测试全自动

每搭完一个就测试一个，确认跑通再搭下一个。
```

---

## 搭建检查清单（第二批）

```
Workflow-C 检查：
  □ 条件分支 action == regenerate 正确分流
  □ 两条分支的 HTTP 获取分镜 URL 包含 shot_id
  □ 原词分支不更新 prompt，编辑分支更新 prompt
  □ 生图引擎 URL 正确

Workflow-D 检查：
  □ 确认分镜的 PUT 请求 URL 正确
  □ 获取已确认分镜带 ?status=confirmed 参数
  □ 合成请求的 Body 是完整 JSON
  □ 合成超时设为 300 秒
  □ 更新段落包含 video_path 和 video_duration

Workflow-E 检查：
  □ 6 个输入变量都有默认值
  □ 合成参数从输入变量读取
  □ subtitle_enabled 的 true/false 字符串比较正确
  □ 与 Workflow-D 的区别：无确认步骤，多了转场/字幕参数

快速模式检查：
  □ 扩写判断逻辑正确（文本长度 < 200）
  □ LLM 扩写的温度设为 0.8
  □ 创建项目并保存的代码中 API 地址正确
  □ 迭代内部 7 个节点连线正确
  □ 自动确认在迭代结束后执行
  □ 合成请求的 shots 数据格式正确
  □ 最终输出包含所有变量
```

第二批全部输出完毕。6 个工作流的手动搭建指南完整交付。