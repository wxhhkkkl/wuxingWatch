#!/usr/bin/env bash
# 生产部署：后台运行 FastAPI，SSH 断开不挂起，日志写入 logs/uvicorn.log。
# 用法：./start_prod.sh [PORT]     （默认 8000，可用 PORT 环境变量覆盖）
# 停止：kill $(cat logs/uvicorn.pid)   （或直接 kill <PID>）
set -e
cd "$(dirname "$0")"

# 首次运行自动安装依赖。
if [ ! -d .venv ]; then
  echo "[backend] 首次运行，正在用 uv 安装依赖..."
  uv sync --extra dev
fi

PORT="${1:-${PORT:-8000}}"
mkdir -p logs
PID_FILE="logs/uvicorn.pid"

if [ -f "$PID_FILE" ] && PID=$(cat "$PID_FILE") && kill -0 "$PID" 2>/dev/null; then
  echo "[backend] 已在运行（PID $PID）。如需重启请先停止：kill \$(cat logs/uvicorn.pid)"
  exit 1
fi

echo "[backend] 后台启动 FastAPI 于 http://localhost:${PORT} （日志：logs/uvicorn.log）"
# nohup + &：忽略 SIGHUP，SSH 断开后进程继续运行。
# 生产环境不带 --reload；如需多进程可加 --workers 4。
nohup uv run uvicorn main:app --app-dir src --host 0.0.0.0 --port "$PORT" \
  > logs/uvicorn.log 2>&1 &
echo $! > "$PID_FILE"
echo "[backend] 已启动，PID $(cat "$PID_FILE")"
