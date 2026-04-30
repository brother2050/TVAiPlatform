import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from shared.config import load_config
from shared.database import get_db
from shared.storage import get_storage
from shared.redis_client import get_redis

from services.project_service.routers import projects, segments, shots, batch


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    cfg = load_config()
    db = get_db()
    db.init_tables()
    get_storage()
    redis_ok = get_redis()
    print(f"[ProjectService] 启动完成")
    print(f"  数据库: {cfg['database']['sqlite_path']}")
    print(f"  存储: {cfg['storage']['local_path']}")
    print(f"  Redis: {'已连接' if redis_ok else '未连接（可选）'}")
    yield
    print("[ProjectService] 关闭")


app = FastAPI(
    title="文章转视频 - 项目管理服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router)
app.include_router(segments.router)
app.include_router(shots.router)
app.include_router(batch.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "project_service"}


if __name__ == "__main__":
    import uvicorn
    cfg = load_config()
    svc = cfg["services"]["project_service"]
    uvicorn.run(
        "services.project_service.app:app",
        host=svc["host"],
        port=svc["port"],
        reload=True,
    )
