param([string]$AlertWebhookUrl = $env:ALERT_WEBHOOK_URL)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$response = Invoke-WebRequest "http://127.0.0.1:8080/api/health/ready" -TimeoutSec 15
if ($response.StatusCode -ne 200) { throw "Readiness endpoint returned HTTP $($response.StatusCode)." }

$unhealthy = docker compose ps --format json | ConvertFrom-Json | Where-Object { $_.Health -and $_.Health -ne "healthy" }
if ($unhealthy) { throw "Unhealthy containers detected: $($unhealthy.Name -join ', ')." }
Write-Host "TenderPulse stack health check passed."
