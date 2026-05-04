#!/usr/bin/env bash
# ============================================================
# 一键停止所有服务
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "  文章转视频 - 停止所有服务"
echo "============================================"
echo ""

stop_service() {
    local name=$1
    local pidfile=$2
    local port=$3

    echo "停止 $name..."

    # 方法 1：通过 PID 文件
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            # 等待进程退出
            for i in $(seq 1 15); do
                if ! kill -0 "$PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # 如果还在运行，强制杀
            if kill -0 "$PID" 2>/dev/null; then
                kill -9 "$PID" 2>/dev/null
                echo -e "  ${YELLOW}$name 强制终止 (PID: $PID)${NC}"
            else
                echo -e "  ${GREEN}$name 已停止 (PID: $PID)${NC}"
            fi
        else
            echo -e "  ${YELLOW}$name PID $PID 已不存在${NC}"
        fi
        rm -f "$pidfile"
    fi

    # 方法 2：通过端口查找（兜底）
    if [ -n "$port" ]; then
        PIDS=$(lsof -ti :"$port" 2>/dev/null || true)
        if [ -n "$PIDS" ]; then
            echo "$PIDS" | xargs kill 2>/dev/null || true
            sleep 2
            PIDS=$(lsof -ti :"$port" 2>/dev/null || true)
            if [ -n "$PIDS" ]; then
                echo "$PIDS" | xargs kill -9 2>/dev/null || true
            fi
            echo -e "  ${GREEN}$name 已通过端口停止${NC}"
        fi
    fi
}
stop_service "ChatTTS服务" "logs/chat_tts_service.pid" "5006"
stop_service "项目管理服务" "logs/project_service.pid" "5005"
stop_service "视频合成服务" "logs/compositor_service.pid" "5004"

echo ""
echo -e "${GREEN}所有服务已停止${NC}"
