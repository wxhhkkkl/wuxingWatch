@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "node_modules" (
    echo [admin] First run: installing dependencies with npm...
    call npm install
)

echo [admin] Starting Vite at http://localhost:5174
call npm run dev -- --host
