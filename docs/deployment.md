## 文件 16：docs/deployment.md

```markdown
# 部署指南

## 环境要求

### 本项目（二次开发代码）

| 项目 | 要求 |
|:---|:---|
| 操作系统 | Linux / macOS / Windows |
| Python | 3.10+ |
| Redis | 6.0+（可选） |
| FFmpeg | 4.0+ |
| 内存 | 8GB+ |
| 磁盘 | 100GB+ 可用空间 |
| GPU / CUDA | **不需要** |

### 外部引擎（独立于本项目）

| 引擎 | GPU 需求 | 说明 |
|:---|:---|:---|
| LLM | 视模型大小 | 可走 API，零 GPU |
| 生图引擎 | 8-24GB 显存 | 视模型选择 |
| 生视频引擎 | 16-24GB+ | 视模型选择 |
| TTS | CPU 可运行 | GPU 加速可选 |

## 本地脚本部署

### 步骤 1：获取代码

```bash
git clone <仓库地址>
cd article-to-video
```

### 步骤 2：环境检查

```bash
chmod +x scripts/*.sh
./scripts/check-env.sh
```

### 步骤 3：初始化

```bash
./scripts/setup-local.sh
```

自动完成：创建虚拟环境、安装依赖、创建目录、初始化数据库。

### 步骤 4：编辑配置

```bash
vim config.yml
```

主要确认：
- Redis 连接信息（如使用）
- 存储路径

### 步骤 5：启动服务

```bash
./scripts/start-all.sh
```

启动后访问：
- 项目管理 API 文档：http://localhost:5005/docs
- 视频合成 API 文档：http://localhost:5003/docs

### 步骤 6：配置 Dify

1. 确认 Dify 已运行
2. 添加 LLM 模型
3. 创建"文章转视频"应用
4. 按 dify-config/workflows/ 下的指南搭建工作流
5. 按 dify-config/tools/ 下的指南注册自定义工具

### 停止服务

```bash
./scripts/stop-all.sh
```

## Docker 部署（远端服务器）

### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  project-service:
    build:
      context: .
      dockerfile: docker/project-service.Dockerfile
    ports:
      - "5005:5005"
    volumes:
      - storage_data:/app/storage
      - db_data:/app/data
    environment:
      - APP_CONFIG=/app/config.yml
    depends_on:
      - redis

  compositor-service:
    build:
      context: .
      dockerfile: docker/compositor-service.Dockerfile
    ports:
      - "5003:5003"
    volumes:
      - storage_data:/app/storage
    environment:
      - APP_CONFIG=/app/config.yml
    depends_on:
      - redis

volumes:
  redis_data:
  storage_data:
  db_data:
```

### Dockerfile 模板

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "services.project_service.app"]
```

## 混合部署

本地机器跑 Dify + 项目管理服务 + 视频合成服务。
远端服务器跑 GPU 密集型引擎（生图、生视频）。

配置方式：在 Dify 自定义工具中将引擎 URL 指向远端服务器地址。
```

---