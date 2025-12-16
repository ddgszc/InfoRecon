#!/bin/bash
# 停止脚本

cd "$(dirname "$0")"

echo "停止服务..."

# 停止 FastAPI 服务
if [ -f logs/api.pid ]; then
    kill $(cat logs/api.pid) 2>/dev/null
    rm -f logs/api.pid
    echo "FastAPI 服务已停止"
fi

# 停止 MCP 服务器
if [ -f logs/mcp.pid ]; then
    kill $(cat logs/mcp.pid) 2>/dev/null
    rm -f logs/mcp.pid
    echo "MCP 服务器已停止"
fi

echo "完成"

