#!/bin/bash
# 启动脚本

cd "$(dirname "$0")"

# 创建日志目录
mkdir -p logs

# 启动 FastAPI 服务
echo "启动 FastAPI 服务 (端口 8000)..."
uv run api_run.py > logs/api.log 2>&1 &
echo $! > logs/api.pid

# 启动 MCP 服务器
echo "启动 MCP 服务器 (端口 33668)..."
uv run mcp_run.py > logs/mcp.log 2>&1 &
echo $! > logs/mcp.pid

echo "所有服务已启动"
echo "停止服务请运行: ./stop.sh"

