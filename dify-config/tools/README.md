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
