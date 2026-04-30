
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
{
  "shot_id": "shot_003",
  "changed_fields": ["dialogue", "prompt"],
  "need_regenerate_image": true,
  "need_regenerate_audio": true,
  "action_required": "regenerate_图片_and_配音",
  "message": "dialogue和prompt已修改，需要重新生成图片和配音"
}
