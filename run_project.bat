@echo off
TITLE TenderPulse 4IR Enterprise Platform Launcher
cd /d "%~dp0"

echo ================================================================
echo    Launching TenderPulse 4IR GovTech & AI Procurement Platform     
echo ================================================================

REM Check if Python AI backend is running on port 8080 or 8000
netstat -ano | findstr /R ":8080\>" >nul
if errorlevel 1 (
    netstat -ano | findstr /R ":8000\>" >nul
    if errorlevel 1 (
        echo [*] Starting Python 3.11 AI Backend (Z3, NetworkX, Sentinel-1)...
        start /min "TenderPulse AI Daemon" run_ai_backend.bat
    ) else (
        echo [*] Python 3.11 AI Backend is actively running on Port 8000.
    )
) else (
    echo [*] Python 3.11 AI Backend is actively running on Port 8080.
)

REM Check if background crawler is running, if not start it minimized
tasklist /FI "IMAGENAME eq powershell.exe" /V | findstr /I "crawler.ps1" >nul
if errorlevel 1 (
    echo [*] Starting 24/7 Background Harvester Daemon...
    start /min "TenderPulse Background Harvester" run_24-7_crawler.bat
) else (
    echo [*] Background Harvester Daemon is actively running.
)

echo [*] Launching TenderPulse 4IR in Default Web Browser...
start "" "http://127.0.0.1:8080/"

echo ================================================================
echo    Platform is running! Keep this window open or minimize.
echo ================================================================
pause
