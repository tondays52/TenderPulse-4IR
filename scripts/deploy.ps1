# ==============================================================================
# TenderPulse 4IR - Automated Production Deployment Script (PowerShell)
# ==============================================================================

param(
    [switch]$BuildOnly,
    [switch]$Down,
    [switch]$Logs
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  TenderPulse 4IR - Production Container Deployment" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if ($Down) {
    Write-Host "[*] Stopping and removing active containers..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "[+] Containers stopped successfully." -ForegroundColor Green
    exit 0
}

if ($Logs) {
    docker-compose logs -f
    exit 0
}

# Verify .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[!] .env not found, generating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# Ensure data directory exists
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" -Force | Out-Null
}

Write-Host "[*] Building Docker images..." -ForegroundColor Yellow
docker-compose build

if ($BuildOnly) {
    Write-Host "[+] Build completed successfully (--BuildOnly specified)." -ForegroundColor Green
    exit 0
}

Write-Host "[*] Starting production stack (App + Nginx + Redis)..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "[*] Waiting for application health check..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/health" -TimeoutSec 10
    if ($health.status -eq "ONLINE") {
        Write-Host "[+] Deployment SUCCESSFUL! Service is ONLINE on http://127.0.0.1:8080/" -ForegroundColor Green
        Write-Host "    Active SMT Solver: $($health.active_ai_engines.smt_solver)" -ForegroundColor Gray
        Write-Host "    Cartel Radar:      $($health.active_ai_engines.cartel_radar)" -ForegroundColor Gray
        Write-Host "    Sentinel Pipeline: $($health.active_ai_engines.sentinel_pipeline)" -ForegroundColor Gray
    } else {
        Write-Host "[!] Unexpected status: $($health.status)" -ForegroundColor Red
    }
} catch {
    Write-Host "[!] Health check failed to respond within 10 seconds. Check logs with: docker-compose logs" -ForegroundColor Red
}
