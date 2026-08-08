#!/usr/bin/env bash
# 启动后台管理端（Vue 3 + Element Plus）。
set -e
cd "$(dirname "$0")"

if [ ! -d node_modules ]; then
  echo "[admin] 首次运行，正在用 npm 安装依赖..."
  npm install
fi

echo "[admin] 启动后台管理端于 http://localhost:5174"
exec npm run dev
