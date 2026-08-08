@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Starting backend :8000 ===
start "wuxingWatch-backend" cmd /k "cd /d %~dp0backend && start.bat"

echo === Starting frontend :5173 ===
start "wuxingWatch-frontend" cmd /k "cd /d %~dp0frontend && start.bat"

echo.
echo Backend  http://localhost:8000  (Docs: /docs)
echo Frontend http://localhost:5173
echo To stop: close the two new windows, or press Ctrl+C in each.
