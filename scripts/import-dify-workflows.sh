#!/usr/bin/env bash
# ============================================================
# Dify 工作流导入脚本（占位）
# 实际导入需要通过 Dify API 或手动在界面中操作
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "  Dify 工作流导入指南"
echo "============================================"
echo ""

DIFY_API="${DIFY_API_BASE:-http://localhost/v1}"
DIFY_KEY="${DIFY_API_KEY:-}"

if [ -z "$DIFY_KEY" ]; then
    echo -e "${YELLOW}未设置 DIFY_API_KEY 环境变量${NC}"
    echo ""
    echo "请手动在 Dify 界面中导入工作流："
    echo ""
    echo "  1. 打开 Dify 界面"
    echo "  2. 进入 工作室 → 创建应用 → 工作流编排"
    echo "  3. 使用「导入DSL」功能，依次导入以下文件："
    echo ""
    echo "     dify-config/workflows/text-preprocessing.json"
    echo "     dify-config/workflows/single-segment-render.json"
    echo "     dify-config/workflows/shot-review-regenerate.json"
    echo "     dify-config/workflows/confirm-and-compose.json"
    echo "     dify-config/workflows/compositor.json"
    echo "     dify-config/workflows/quick-mode.json"
    echo ""
    echo "  4. 注册自定义工具（参考 dify-config/tools/ 目录下的说明）"
    echo ""
    exit 0
fi

echo "Dify API: $DIFY_API"
echo ""

# 通过 API 导入（需要 Dify API Key）
for workflow_file in dify-config/workflows/*.json; do
    if [ -f "$workflow_file" ]; then
        filename=$(basename "$workflow_file" .json)
        echo "导入 $filename ..."

        # Dify 导入 API（具体端点可能因 Dify 版本不同而变化）
        response=$(curl -s -X POST "$DIFY_API/apps/import" \
            -H "Authorization: Bearer $DIFY_KEY" \
            -H "Content-Type: application/json" \
            -d @"$workflow_file" 2>/dev/null)

        if echo "$response" | grep -q '"id"'; then
            echo -e "  ${GREEN}✓ $filename 导入成功${NC}"
        else
            echo -e "  ${YELLOW}! $filename 可能需要手动导入${NC}"
        fi
    fi
done

echo ""
echo "============================================"
echo -e "  ${GREEN}导入完成${NC}"
echo "  请在 Dify 界面中确认工作流和工具配置"
echo "============================================"
