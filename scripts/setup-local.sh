#!/usr/bin/env bash
# ============================================================
# 本地初始化脚本
# 创建虚拟环境、安装依赖、初始化目录和数据库
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "  文章转视频 - 本地初始化"
echo "============================================"
echo ""

# ── 步骤 1：创建虚拟环境 ──
echo "[1/6] 创建 Python 虚拟环境..."
if [ -d ".venv" ]; then
    echo -e "  ${YELLOW}venv 目录已存在，跳过创建${NC}"
else
    python3.11 -m venv .venv
    echo -e "  ${GREEN}虚拟环境已创建${NC}"
fi

# 激活虚拟环境
source .venv/bin/activate

# ── 步骤 2：安装依赖 ──
echo "[2/6] 安装 Python 依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "  ${GREEN}依赖安装完成${NC}"

# ── 步骤 3：创建目录结构 ──
echo "[3/6] 创建目录结构..."
mkdir -p data
mkdir -p storage
mkdir -p logs
echo -e "  ${GREEN}目录创建完成${NC} (data/, storage/, logs/)"

# ── 步骤 4：生成配置文件 ──
echo "[4/6] 检查配置文件..."
if [ -f "config.yml" ]; then
    echo -e "  ${YELLOW}config.yml 已存在，跳过生成${NC}"
else
    echo -e "  ${YELLOW}请手动创建 config.yml 或从 config.yml.example 复制${NC}"
fi

# ── 步骤 5：初始化数据库 ──
echo "[5/6] 初始化数据库..."
if [ -f "scripts/init_db.sql" ]; then
    python3 -c "
from shared.config import load_config
from shared.database import get_db
cfg = load_config()
db = get_db()
db.init_tables('scripts/init_db.sql')
print('  数据库初始化完成: ' + cfg['database']['sqlite_path'])
"
else
    python3 -c "
from shared.config import load_config
from shared.database import get_db
cfg = load_config()
db = get_db()
db.init_tables()
print('  数据库初始化完成: ' + cfg['database']['sqlite_path'])
"
fi

# ── 步骤 6：验证 ──
echo "[6/6] 验证安装..."
python3 -c "
from shared.config import load_config
from shared.database import get_db
from shared.storage import get_storage
cfg = load_config()
db = get_db()
storage = get_storage()
print('  配置加载: OK')
print('  数据库连接: OK')
print('  存储目录: OK')
"

echo ""
echo "============================================"
echo -e "  ${GREEN}初始化完成！${NC}"
echo ""
echo "  接下来："
echo "  1. 检查并编辑 config.yml（如需要）"
echo "  2. 运行 scripts/start-all.sh 启动服务"
echo "============================================"
