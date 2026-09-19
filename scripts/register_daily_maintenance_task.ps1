param([string]$Time = "02:30", [int]$RetentionDays = 14)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$script = Join-Path $PSScriptRoot "run_daily_maintenance.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`" -RetentionDays $RetentionDays"
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
Register-ScheduledTask -TaskName "TenderPulseDailyMaintenance" -Action $action -Trigger $trigger -Description "TenderPulse PostgreSQL backup and readiness check" -Force | Out-Null
Write-Host "Scheduled daily TenderPulse maintenance at $Time."
