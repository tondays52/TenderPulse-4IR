param([Parameter(Mandatory = $true)][string]$BackupPath)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$resolvedBackup = (Resolve-Path -LiteralPath $BackupPath).Path
$containerId = (docker compose ps -q postgres).Trim()
if (-not $containerId) { throw "PostgreSQL container is not running." }

$restoreDb = "tenderpulse_restore_verify_" + (Get-Date -Format "yyyyMMddHHmmss")
$containerBackup = "/tmp/restore-$(Get-Date -Format 'yyyyMMddHHmmss').dump"
try {
    docker cp $resolvedBackup "${containerId}:$containerBackup"
    docker compose exec -T -e RESTORE_DB=$restoreDb postgres sh -c 'createdb -U "$POSTGRES_USER" "$RESTORE_DB"'
    docker compose exec -T -e RESTORE_DB=$restoreDb postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$RESTORE_DB" --exit-on-error "$1"' -- $containerBackup
    $tableCount = (docker compose exec -T -e RESTORE_DB=$restoreDb postgres sh -c 'psql -U "$POSTGRES_USER" -d "$RESTORE_DB" -tAc "select count(*) from information_schema.tables where table_schema = current_schema()"').Trim()
    if ([int]$tableCount -lt 1) { throw "Restore did not create application tables." }
    Write-Host "Restore verification passed: $tableCount tables restored into disposable database $restoreDb."
} finally {
    docker compose exec -T -e RESTORE_DB=$restoreDb postgres sh -c 'dropdb -U "$POSTGRES_USER" --if-exists "$RESTORE_DB"' | Out-Null
    docker compose exec -T postgres rm -f $containerBackup | Out-Null
}
