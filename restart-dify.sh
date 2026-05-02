#!/bin/bash

# ============================================
# Dify macOS Restart Script
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "Restarting Dify..."
echo ""

"$SCRIPT_DIR/stop-dify.sh"
sleep 3
"$SCRIPT_DIR/start-dify.sh"
