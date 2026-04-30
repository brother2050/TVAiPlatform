
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
