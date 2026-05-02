#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}=== Stopping Dify ===${NC}\n"

# API
if [ -f /tmp/dify-api.pid ]; then
  kill $(cat /tmp/dify-api.pid) 2>/dev/null && echo -e "  ${GREEN}[OK]${NC} API server stopped" || echo -e "  ${YELLOW}[WARN]${NC} API server was not running"
  rm -f /tmp/dify-api.pid
else
  pkill -f "gunicorn.*app:create_app" 2>/dev/null && echo -e "  ${GREEN}[OK]${NC} API server stopped" || echo -e "  ${YELLOW}[WARN]${NC} API server was not running"
fi

# Celery
pkill -f "celery.*app.celery" 2>/dev/null && echo -e "  ${GREEN}[OK]${NC} Celery worker stopped" || echo -e "  ${YELLOW}[WARN]${NC} Celery worker was not running"

# Web
pkill -f "next dev" 2>/dev/null && echo -e "  ${GREEN}[OK]${NC} Web frontend stopped" || echo -e "  ${YELLOW}[WARN]${NC} Web frontend was not running"

echo -e "\n  ${GREEN}All Dify services stopped.${NC}\n"
