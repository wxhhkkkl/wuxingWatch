# 启动前端（Vue 3 + Vite 开发服务器）。
# 用法：在 PowerShell 中执行 .\start.ps1
Set-Location $PSScriptRoot

# 首次运行自动安装依赖。
if (-not (Test-Path node_modules)) {
    Write-Host "[frontend] 首次运行，正在用 npm 安装依赖..."
    npm install
}

Write-Host "[frontend] 启动 Vite 于 http://localhost:5173"
# --host 允许手机等局域网设备访问；API 已由 Vite 代理到后端 :8000。
npm run dev -- --host
