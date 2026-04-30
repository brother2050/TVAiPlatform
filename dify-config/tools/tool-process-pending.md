
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
{
  "project_id": "proj_001",
  "pending_image_tasks": 5,
  "pending_audio_tasks": 3,
  "pending_compose_tasks": 2,
  "total_tasks": 10,
  "estimated_time_seconds": 210,
  "message": "已提交 10 个任务到处理队列"
}
