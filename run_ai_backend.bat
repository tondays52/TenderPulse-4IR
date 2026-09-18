@echo off
chcp 65001 >nul
title TenderPulse 4IR AI Engine - FastAPI Daemon (Port 8000)

echo =====================================================================
echo   TenderPulse 4IR AI Engine - Autonomous Procurement Intelligence
echo   Powered by Python 3.11, Microsoft Z3 SMT, NetworkX and Sentinel-1
echo =====================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv not found. Please install Python 3.11 first.
    pause
    exit /b 1
)

echo [*] Starting FastAPI Local AI Daemon on http://127.0.0.1:8000 ...
echo [*] Interactive Swagger Docs available at: http://127.0.0.1:8000/docs
echo.

".venv\Scripts\python.exe" -m uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
pause
