@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv" (
    echo [backend] First run: installing dependencies with uv...
    uv sync --extra dev
)

if "%PORT%"=="" set PORT=8000
echo [backend] Starting FastAPI at http://localhost:%PORT%  (Docs: /docs)
echo [backend] To change port: set PORT=8001 ^& start.bat  (and update frontend Vite proxy)
uv run uvicorn main:app --app-dir src --reload --host 0.0.0.0 --port %PORT%
