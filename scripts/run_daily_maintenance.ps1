param([int]$RetentionDays = 14)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
try {
    & (Join-Path $PSScriptRoot "backup_postgres.ps1") -RetentionDays $RetentionDays
    & (Join-Path $PSScriptRoot "check_stack_health.ps1")
} catch {
    Write-Error "TenderPulse daily maintenance failed: $($_.Exception.Message)"
    exit 1
}
