#!/usr/bin/env bash
# ============================================================
# 一键启动所有服务
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "  文章转视频 - 启动所有服务"
echo "============================================"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "虚拟环境不存在，请先运行 scripts/setup-local.sh"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 确保日志目录存在
mkdir -p logs

# ── 启动项目管理服务 ──
echo "[1/2] 启动项目管理服务 (端口 5005)..."
if lsof -i :5005 &>/dev/null; then
    echo -e "  ${YELLOW}端口 5005 已被占用，跳过${NC}"
else
    nohup python3 -m services.project_service.app \
        > logs/project_service.log 2>&1 &
    PID1=$!
    echo "$PID1" > logs/project_service.pid
    echo -e "  ${GREEN}项目管理服务已启动 (PID: $PID1)${NC}"
    echo "  日志: logs/project_service.log"
fi

# ── 启动视频合成服务 ──
echo "[2/2] 启动视频合成服务 (端口 5004)..."
if lsof -i :5004 &>/dev/null; then
    echo -e "  ${YELLOW}端口 5004 已被占用，跳过${NC}"
else
    nohup python3 -m services.compositor.app \
        > logs/compositor_service.log 2>&1 &
    PID2=$!
    echo "$PID2" > logs/compositor_service.pid
    echo -e "  ${GREEN}视频合成服务已启动 (PID: $PID2)${NC}"
    echo "  日志: logs/compositor_service.log"
fi

# ── 等待服务就绪 ──
echo ""
echo "等待服务就绪..."
sleep 3

# ── 健康检测 ──
echo ""
echo "健康检测："

if curl -s http://localhost:5005/health | grep -q "healthy"; then
    echo -e "  ${GREEN}✓ 项目管理服务 (5005)${NC}"
else
    echo -e "  ${YELLOW}! 项目管理服务启动中...请稍后检查${NC}"
fi

if curl -s http://localhost:5004/health | grep -q "healthy"; then
    echo -e "  ${GREEN}✓ 视频合成服务 (5004)${NC}"
else
    echo -e "  ${YELLOW}! 视频合成服务启动中...请稍后检查${NC}"
fi

echo ""
echo "============================================"
echo -e "  ${GREEN}服务启动完成${NC}"
echo ""
echo "  API 文档："
echo "    项目管理: http://localhost:5005/docs"
echo "    视频合成: http://localhost:5004/docs"
echo ""
echo "  停止服务：scripts/stop-all.sh"
echo "  查看日志：tail -f logs/*.log"
echo "============================================"
