#!/usr/bin/env bash
# 启动后端（FastAPI，开发模式带热重载）。
# 用法：./start.sh   或在项目根目录执行 ./start.sh 自动同时启动前后端。
set -e
cd "$(dirname "$0")"

# 首次运行自动安装依赖（含测试/开发依赖）。
if [ ! -d .venv ]; then
  echo "[backend] 首次运行，正在用 uv 安装依赖..."
  uv sync --extra dev
fi

PORT="${PORT:-8000}"
echo "[backend] 启动 FastAPI 于 http://localhost:${PORT} （Docs: /docs）"
echo "[backend] 提示：端口被占用时可用 PORT=8001 ./start.sh 换端口（前端 Vite 代理需同步改）。"
# --app-dir src：让 src 进入 import 路径；--host 0.0.0.0 允许手机等局域网设备访问。
exec uv run uvicorn main:app --app-dir src --reload --host 0.0.0.0 --port "$PORT"
