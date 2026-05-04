"""ChatTTS 服务主应用"""

import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch

from shared.config import load_config
from services.chattts.router import router as chattts_router
from services.chattts.core import init_engine
from services.chattts.voices import get_voice_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("[ChatTTS Service] 启动中...")
    
    # 加载配置
    cfg = load_config()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # 初始化音色管理器
    voice_manager = get_voice_manager()
    print(f"[ChatTTS Service] 已加载 {len(voice_manager.list_presets())} 个预存音色")
    
    # 懒加载 ChatTTS 模型（首次请求时初始化）
    print(f"[ChatTTS Service] 设备: {device}")
    print(f"[ChatTTS Service] 启动完成（模型将在首次请求时加载）")
    
    yield
    
    print("[ChatTTS Service] 关闭")


app = FastAPI(
    title="ChatTTS 语音合成服务",
    description="""
## ChatTTS 语音合成 API

提供基于 ChatTTS 的文本转语音功能，支持：

### 核心功能
- **语音合成**: 将文本转换为自然语音
- **音色控制**: 支持 seed 和预存音色
- **参数配置**: 灵活的推理和文本优化参数

### 参数说明
- `temperature`: 采样温度，控制随机性
- `top_P`: 核采样阈值
- `top_K`: Top-K 采样数量
- `oral`: 口语化程度
- `break`: 停顿标记强度

### 返回格式
- `file`: 返回文件路径
- `base64`: 返回 Base64 编码的音频
- `bytes`: 直接返回 WAV 字节流
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chattts_router)


@app.get("/health")
def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "chattts",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    cfg = load_config()
    
    # ChatTTS 服务默认端口
    port = cfg["services"].get("chattts_service", {}).get("port", 5006)
    host = cfg["services"].get("chattts_service", {}).get("host", "0.0.0.0")
    
    uvicorn.run(
        "services.chattts.app:app",
        host=host,
        port=port,
        reload=True,
    )
