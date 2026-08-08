#!/usr/bin/env bash
# 一键同时启动后端（:8000）与前端（:5173）。
# 用法：./start.sh
# 停止：按 Ctrl+C。
set -e
cd "$(dirname "$0")"

echo "=== 启动后端 :8000 ==="
./backend/start.sh &
BACK_PID=$!

echo "=== 启动前端 :5173 ==="
./frontend/start.sh &
FRONT_PID=$!

trap 'echo "正在停止服务..."; kill "$BACK_PID" "$FRONT_PID" 2>/dev/null' INT TERM EXIT
wait
