# 启动后端（FastAPI，开发模式带热重载）。
# 用法：在 PowerShell 中执行 .\start.ps1
Set-Location $PSScriptRoot

# 首次运行自动安装依赖（含测试/开发依赖）。
if (-not (Test-Path .venv)) {
    Write-Host "[backend] 首次运行，正在用 uv 安装依赖..."
    uv sync --extra dev
}

$port = if ($env:PORT) { $env:PORT } else { "8000" }
Write-Host "[backend] 启动 FastAPI 于 http://localhost:$port （Docs: /docs）"
Write-Host "[backend] 提示：端口被占用时可用 `$env:PORT='8001'; .\start.ps1 换端口（前端 Vite 代理需同步改）。"
# --app-dir src：让 src 进入 import 路径；--host 0.0.0.0 允许手机等局域网设备访问。
uv run uvicorn main:app --app-dir src --reload --host 0.0.0.0 --port $port
