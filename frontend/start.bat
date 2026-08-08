@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "node_modules" (
    echo [frontend] First run: installing dependencies with npm...
    call npm install
)

echo [frontend] Starting Vite at http://localhost:5173
call npm run dev -- --host
