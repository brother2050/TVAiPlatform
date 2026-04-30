
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
{
  "action": "edit_and_regenerate",
  "new_prompt": "A young man sitting at office desk, opening a mysterious letter, red desk lamp, warm lighting",
  "new_negative_prompt": "blurry, low quality, deformed"
}
响应格式
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