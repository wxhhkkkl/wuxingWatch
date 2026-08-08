#!/usr/bin/env bash
# 启动前端（Vue 3 + Vite 开发服务器）。
# 用法：./start.sh   或在项目根目录执行 ./start.sh 自动同时启动前后端。
set -e
cd "$(dirname "$0")"

# 首次运行自动安装依赖。
if [ ! -d node_modules ]; then
  echo "[frontend] 首次运行，正在用 npm 安装依赖..."
  npm install
fi

echo "[frontend] 启动 Vite 于 http://localhost:5173"
# --host 允许手机等局域网设备访问；API 已由 Vite 代理到后端 :8000。
exec npm run dev -- --host
