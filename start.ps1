# 一键同时启动后端（:8000）与前端（:5173）。
# 用法：在 PowerShell 中执行 .\start.ps1
# 停止：关闭两个窗口，或分别 Ctrl+C。
Write-Host "=== 启动后端 :8000 ==="
Start-Process powershell -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass",
    "-File", "$PSScriptRoot\backend\start.ps1"
)

Write-Host "=== 启动前端 :5173 ==="
Start-Process powershell -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass",
    "-File", "$PSScriptRoot\frontend\start.ps1"
)

Write-Host "两个服务已在新窗口启动：后端 http://localhost:8000，前端 http://localhost:5173"
