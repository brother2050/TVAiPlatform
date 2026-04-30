#!/usr/bin/env bash
# ============================================================
# 环境检查脚本
# 检查项目运行所需的所有依赖
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "  ${YELLOW}!${NC} $1"
    ((WARN++))
}

echo "============================================"
echo "  文章转视频 - 环境检查"
echo "============================================"
echo ""

# ── Python ──
echo "[Python]"
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        check_pass "Python $PY_VERSION"
    else
        check_fail "Python $PY_VERSION (需要 3.10+)"
    fi
else
    check_fail "Python3 未安装"
fi

# ── pip ──
echo "[pip]"
if command -v pip3 &> /dev/null; then
    check_pass "pip3 已安装"
elif command -v pip &> /dev/null; then
    check_pass "pip 已安装"
else
    check_fail "pip 未安装"
fi

# ── FFmpeg ──
echo "[FFmpeg]"
if command -v ffmpeg &> /dev/null; then
    FF_VERSION=$(ffmpeg -version 2>&1 | head -n1)
    check_pass "$FF_VERSION"
else
    check_fail "FFmpeg 未安装 (sudo apt install ffmpeg / brew install ffmpeg)"
fi

# ── FFprobe ──
echo "[FFprobe]"
if command -v ffprobe &> /dev/null; then
    check_pass "ffprobe 已安装"
else
    check_fail "ffprobe 未安装 (通常随 FFmpeg 一起安装)"
fi

# ── Redis (可选) ──
echo "[Redis] (可选)"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        check_pass "Redis 已运行"
    else
        check_warn "Redis 已安装但未运行 (redis-server &)"
    fi
else
    check_warn "Redis 未安装 (可选，不影响核心功能)"
fi

# ── Dify ──
echo "[Dify] (外部服务)"
DIFY_URL="${DIFY_URL:-http://localhost}"
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$DIFY_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "000" ]; then
        check_pass "Dify 可访问 ($DIFY_URL → HTTP $HTTP_CODE)"
    else
        check_warn "Dify 不可访问 ($DIFY_URL) — 请确认 Dify 已启动"
    fi
else
    check_warn "curl 未安装，无法检测 Dify"
fi

# ── 磁盘空间 ──
echo "[磁盘空间]"
AVAIL_GB=$(df -BG . | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$AVAIL_GB" -ge 10 ]; then
    check_pass "可用空间 ${AVAIL_GB}GB"
else
    check_warn "可用空间仅 ${AVAIL_GB}GB (建议 10GB+)"
fi

# ── 内存 ──
echo "[内存]"
if command -v free &> /dev/null; then
    MEM_TOTAL=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$MEM_TOTAL" -ge 8 ]; then
        check_pass "总内存 ${MEM_TOTAL}GB"
    else
        check_warn "总内存 ${MEM_TOTAL}GB (建议 8GB+)"
    fi
elif [ "$(uname)" = "Darwin" ]; then
    MEM_BYTES=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
    MEM_GB=$((MEM_BYTES / 1073741824))
    if [ "$MEM_GB" -ge 8 ]; then
        check_pass "总内存 ${MEM_GB}GB"
    else
        check_warn "总内存 ${MEM_GB}GB (建议 8GB+)"
    fi
fi

# ── 汇总 ──
echo ""
echo "============================================"
echo "  检查结果: ${GREEN}${PASS} 通过${NC}  ${RED}${FAIL} 失败${NC}  ${YELLOW}${WARN} 警告${NC}"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}存在未通过的检查项，请先修复后再运行 setup-local.sh${NC}"
    exit 1
else
    echo -e "${GREEN}环境检查通过，可以运行 setup-local.sh${NC}"
    exit 0
fi
