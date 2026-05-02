#!/bin/bash
set -e

# ============================================================
#  Dify Local Development — Start Script
#  macOS / Homebrew environment
# ============================================================

# ——— Colors ————————————————————————————————————————————————
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; exit 1; }
step() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

# ——— Configuration ———————————————————————————————————————————
DIFY_HOME="/Users/andrew/workspace/TVAiPlatform/dify"
API_DIR="${DIFY_HOME}/api"
WEB_DIR="${DIFY_HOME}/web"
VENV_DIR="${API_DIR}/.venv"

DB_NAME="dify"
DB_USER="andrew"
DB_HOST="localhost"
DB_PORT="5432"

REDIS_HOST="localhost"
REDIS_PORT="6379"

API_HOST="0.0.0.0"
API_PORT="5001"

WEB_PORT="3000"

# ——— 1. LLVM 20 —————————————————————————————————————————————
step "LLVM 20"
export PATH="/usr/local/opt/llvm@20/bin:$PATH"
export LLVM_DIR="/usr/local/opt/llvm@20/lib/cmake/llvm"
export CMAKE_PREFIX_PATH="/usr/local/opt/llvm@20"
export LDFLAGS="-L/usr/local/opt/llvm@20/lib"
export CPPFLAGS="-I/usr/local/opt/llvm@20/include"

if command -v llvm-config &>/dev/null; then
  LLVM_VER=$(llvm-config --version 2>/dev/null || true)
  if [[ "$LLVM_VER" == 20.* ]]; then
    ok "LLVM ${LLVM_VER} configured"
  else
    fail "Expected LLVM 20.x, found '${LLVM_VER}'. Run: brew install llvm@20"
  fi
else
  fail "llvm-config not found. Run: brew install llvm@20"
fi

# ——— 2. PostgreSQL —————————————————————————————————————————
step "PostgreSQL"

if ! command -v pg_isready &>/dev/null; then
  fail "pg_isready not found. Is PostgreSQL installed?"
fi

if pg_isready -h "$DB_HOST" -p "$DB_PORT" &>/dev/null; then
  ok "PostgreSQL is running on port ${DB_PORT}"
else
  warn "PostgreSQL is not running, attempting to start..."
  if command -v brew &>/dev/null; then
    brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null || true
    sleep 3
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" &>/dev/null; then
      ok "PostgreSQL started"
    else
      fail "Could not start PostgreSQL. Start it manually."
    fi
  else
    fail "Start PostgreSQL manually."
  fi
fi

# Verify database exists
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt 2>/dev/null | grep -q " ${DB_NAME} "; then
  ok "Database '${DB_NAME}' exists (user: ${DB_USER})"
else
  warn "Database '${DB_NAME}' not found, creating..."
  createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null || true
  ok "Database '${DB_NAME}' ready"
fi

# ——— 3. Redis ———————————————————————————————————————————————
step "Redis"

if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &>/dev/null; then
  ok "Redis is running on port ${REDIS_PORT}"
else
  warn "Redis is not running, attempting to start..."
  if command -v brew &>/dev/null; then
    brew services start redis 2>/dev/null || true
    sleep 2
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &>/dev/null; then
      ok "Redis started"
    else
      fail "Could not start Redis. Start it manually."
    fi
  else
    fail "Start Redis manually."
  fi
fi

# ——— 4. Virtualenv & Dependencies ———————————————————————————
step "Python Virtual Environment"

if [ ! -d "$VENV_DIR" ]; then
  warn "Virtualenv not found, creating..."
  python3 -m venv "$VENV_DIR"
  ok "Virtualenv created at ${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
ok "Activated virtualenv ($(python3 --version))"

# ——— 5. .env File ———————————————————————————————————————————
step "Environment File"

ENV_FILE="${API_DIR}/.env"

if [ ! -f "$ENV_FILE" ]; then
  warn ".env not found, creating from .env.example..."
  if [ -f "${API_DIR}/.env.example" ]; then
    cp "${API_DIR}/.env.example" "$ENV_FILE"
    ok ".env created from .env.example"
  else
    cat > "$ENV_FILE" <<'ENVEOF'
# ---- Core ----
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=sk-local-dev-change-me-in-production
CONSOLE_WEB_URL=http://localhost:3000
CONSOLE_API_URL=http://localhost:5001
SERVICE_API_URL=http://localhost:5001
APP_WEB_URL=http://localhost:3000

# ---- Database ----
DB_USERNAME=andrew
DB_PASSWORD=201313030065
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=dify

# ---- Redis ----
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ---- Celery ----
CELERY_BROKER_URL=redis://localhost:6379/1
BROKER_USE_SSL=false

# ---- Storage ----
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=storage

# ---- Vector Store (default: weaviate via docker or qdrant) ----
VECTOR_STORE=weaviate

# ---- Others ----
LOG_LEVEL=INFO
ENVEOF
    ok ".env created with defaults"
  fi
else
  ok ".env already exists"
fi

# ——— 6. Database Migration ———————————————————————————————————
step "Database Migration"

cd "$API_DIR"
export FLASK_APP=app

flask db upgrade 2>/dev/null && ok "Database migrated" || warn "Migration skipped or already up to date"

# ——— 7. Start API Server ———————————————————————————————————
step "Starting API Server"

cd "$API_DIR"

# Kill any existing process on the API port
if lsof -ti :"$API_PORT" &>/dev/null; then
  warn "Port ${API_PORT} in use, killing existing process..."
  kill $(lsof -ti :"$API_PORT") 2>/dev/null || true
  sleep 1
fi

# Start gunicorn in background
nohup gunicorn \
  --bind "${API_HOST}:${API_PORT}" \
  --workers 2 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --pid /tmp/dify-api.pid \
  "app:create_app()" \
  > /tmp/dify-api.log 2>&1 &

API_PID=$!
sleep 2

if kill -0 $API_PID 2>/dev/null; then
  ok "API server running on http://${API_HOST}:${API_PORT} (PID: $API_PID)"
else
  fail "API server failed to start. Check /tmp/dify-api.log"
fi

# ——— 8. Start Celery Worker —————————————————————————————————
step "Starting Celery Worker"

cd "$API_DIR"
source "${VENV_DIR}/bin/activate"

# Kill any existing celery
pkill -f "celery.*dify" 2>/dev/null || true
sleep 1

nohup celery \
  -A app.celery \
  worker \
  --loglevel=INFO \
  --concurrency=1 \
  --max-tasks-per-child=100 \
  -Q dataset,generation,mail,ops_trace,app_deletion \
  > /tmp/dify-worker.log 2>&1 &

WORKER_PID=$!
sleep 2

if kill -0 $WORKER_PID 2>/dev/null; then
  ok "Celery worker running (PID: $WORKER_PID)"
else
  warn "Celery worker may have failed. Check /tmp/dify-worker.log"
fi

# ——— 9. Start Web Frontend —————————————————————————————————
step "Starting Web Frontend"

cd "$WEB_DIR"

if [ ! -d "node_modules" ]; then
  warn "node_modules not found, installing dependencies..."
  if command -v pnpm &>/dev/null; then
    pnpm install
  elif command -v npm &>/dev/null; then
    npm install
  else
    fail "Neither pnpm nor npm found. Install Node.js first."
  fi
  ok "Frontend dependencies installed"
fi

# Kill any existing process on the web port
if lsof -ti :"$WEB_PORT" &>/dev/null; then
  warn "Port ${WEB_PORT} in use, killing existing process..."
  kill $(lsof -ti :"$WEB_PORT") 2>/dev/null || true
  sleep 1
fi

if command -v pnpm &>/dev/null; then
  nohup pnpm dev > /tmp/dify-web.log 2>&1 &
elif command -v npm &>/dev/null; then
  nohup npm run dev > /tmp/dify-web.log 2>&1 &
fi

WEB_PID=$!
sleep 3

if kill -0 $WEB_PID 2>/dev/null; then
  ok "Web frontend running on http://localhost:${WEB_PORT} (PID: $WEB_PID)"
else
  warn "Web frontend may still be starting. Check /tmp/dify-web.log"
fi

# ——— 10. Summary ———————————————————————————————————————————
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Dify is up and running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  Web UI:     ${CYAN}http://localhost:${WEB_PORT}${NC}"
echo -e "  API:        ${CYAN}http://localhost:${API_PORT}${NC}"
echo -e "  API Docs:   ${CYAN}http://localhost:${API_PORT}/api/docs${NC}"
echo ""
echo -e "  Logs:"
echo -e "    API:      ${YELLOW}/tmp/dify-api.log${NC}"
echo -e "    Worker:   ${YELLOW}/tmp/dify-worker.log${NC}"
echo -e "    Web:      ${YELLOW}/tmp/dify-web.log${NC}"
echo ""
echo -e "  PIDs:"
echo -e "    API:      ${API_PID}"
echo -e "    Worker:   ${WORKER_PID}"
echo -e "    Web:      ${WEB_PID}"
echo ""
echo -e "  To stop all:  ${CYAN}bash stop-dify.sh${NC}"
echo ""
