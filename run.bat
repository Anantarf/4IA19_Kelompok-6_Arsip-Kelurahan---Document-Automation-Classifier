@echo off
title Document Automation Launcher
echo [INFO] Starting Application...

:: Backend
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv .venv
)
start "Backend" cmd /k "call .venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --host 127.0.0.1 --port 8001"

:: Frontend
cd frontend
if not exist "node_modules" (
    echo [INFO] Installing Frontend dependencies...
    call npm install
)
start "Frontend" cmd /k "npm run dev"
cd ..
