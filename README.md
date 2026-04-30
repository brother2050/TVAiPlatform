## 文件 19：README.md

```markdown
# 文章转视频

基于 Dify 平台二次开发的模块化内容生产系统，专注于将长篇多章文章自动转化为分章短视频。

## 特性

- **三种拆分模式**：自动拆分、手动标记拆分、逐段粘贴
- **五层独立编辑**：段落文本、分镜脚本、分镜图片、配音、合成参数，每层可单独修改
- **分镜审核**：渲染后逐帧审核，不满意可重生成、修改提示词重生成、上传替换
- **联动影响**：修改一处自动判断下游影响，支持批量处理
- **引擎无关**：通过 Dify 接入任意 LLM/生图/TTS 引擎，新增引擎只需改配置
- **Dify 驱动**：所有业务流程通过 Dify 工作流编排，可视化可控

## 架构

```
Dify 平台（编排中枢）
    ↓ HTTP 调用
二次开发服务（项目管理 + 视频合成）
    ↓ HTTP 调用
外部引擎（生图 / TTS / LLM，独立部署）
```

## 快速开始

```bash
# 1. 环境检查
./scripts/check-env.sh

# 2. 初始化
./scripts/setup-local.sh

# 3. 启动服务
./scripts/start-all.sh

# 4. 在 Dify 中配置工作流和工具（参考 dify-config/）

# 5. 开始使用
```

## 目录结构

```
├── config.yml                  配置文件
├── requirements.txt            Python 依赖
├── shared/                     共享工具库
├── services/
│   ├── project_service/        项目管理服务（端口 5005）
│   └── compositor/             视频合成服务（端口 5003）
├── dify-config/
│   ├── tools/                  Dify 自定义工具配置说明
│   └── workflows/              Dify 工作流搭建指南
├── scripts/                    部署脚本
├── docs/                       文档
├── data/                       数据库文件（自动生成）
├── storage/                    媒体文件存储（自动生成）
└── logs/                       日志文件（自动生成）
```

## 文档

- [部署指南](docs/deployment.md)
- [API 速查](docs/api-reference.md)
- [问题排查](docs/troubleshooting.md)
- [Dify 工具配置](dify-config/tools/README.md)
- [Dify 工作流搭建](dify-config/workflows/README.md)

## 技术栈

| 组件 | 选型 |
|:---|:---|
| 平台 | Dify 社区版 |
| 后端框架 | FastAPI |
| 数据库 | SQLite / PostgreSQL |
| 任务队列 | Redis（可选） |
| 视频处理 | FFmpeg |
| 图像处理 | Pillow |

## 项目状态

- [x] Part 1：基础设施 + 项目管理服务
- [x] Part 2：视频合成服务 + 部署脚本
- [x] Part 3：Dify 配置 + 文档
```

---

## Part 3 交付物清单

```
已交付：
  ✅ dify-config/tools/README.md               工具配置总览
  ✅ dify-config/tools/tool-generate-image.md   生图工具
  ✅ dify-config/tools/tool-generate-speech.md  TTS 工具
  ✅ dify-config/tools/tool-save-project-data.md 项目数据工具
  ✅ dify-config/tools/tool-compose-video.md    视频合成工具
  ✅ dify-config/tools/tool-regenerate-shot.md  分镜重生成工具
  ✅ dify-config/tools/tool-edit-shot-script.md 分镜编辑工具
  ✅ dify-config/tools/tool-process-pending.md  批量处理工具
  ✅ dify-config/workflows/README.md            工作流总览
  ✅ dify-config/workflows/workflow-a.md        Workflow-A 搭建指南
  ✅ dify-config/workflows/workflow-b.md        Workflow-B 搭建指南
  ✅ dify-config/workflows/workflow-c.md        Workflow-C 搭建指南
  ✅ dify-config/workflows/workflow-d.md        Workflow-D 搭建指南
  ✅ dify-config/workflows/workflow-e.md        Workflow-E 搭建指南
  ✅ dify-config/workflows/workflow-quick.md    快速模式搭建指南
  ✅ docs/deployment.md                         部署指南
  ✅ docs/api-reference.md                      API 速查
  ✅ docs/troubleshooting.md                    问题排查
  ✅ README.md                                  项目说明
```

---

## 三个 Part 总交付汇总

```
Part 1（基础设施 + 项目管理服务）：
  ✅ requirements.txt
  ✅ config.yml
  ✅ shared/config.py
  ✅ shared/database.py
  ✅ shared/storage.py
  ✅ shared/redis_client.py
  ✅ services/project_service/models.py
  ✅ services/project_service/db.py
  ✅ services/project_service/routers/projects.py
  ✅ services/project_service/routers/segments.py
  ✅ services/project_service/routers/shots.py
  ✅ services/project_service/routers/batch.py
  ✅ services/project_service/app.py
  ✅ scripts/init_db.sql

Part 2（视频合成服务 + 部署脚本）：
  ✅ services/compositor/models.py
  ✅ services/compositor/subtitle.py
  ✅ services/compositor/title_card.py
  ✅ services/compositor/transition.py
  ✅ services/compositor/audio_mixer.py
  ✅ services/compositor/video_builder.py
  ✅ services/compositor/app.py
  ✅ scripts/check-env.sh
  ✅ scripts/setup-local.sh
  ✅ scripts/start-all.sh
  ✅ scripts/stop-all.sh
  ✅ scripts/import-dify-workflows.sh

Part 3（Dify 配置 + 文档）：
  ✅ dify-config/tools/（8 个文件）
  ✅ dify-config/workflows/（7 个文件）
  ✅ docs/（3 个文件）
  ✅ README.md

总计：42 个文件，覆盖里程碑 1 全部设计。
```

三个 Part 全部输出完毕，按此内容创建文件即可启动项目。