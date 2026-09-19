param(
    [int]$RetentionDays = 14,
    [string]$BackupDirectory = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
if (-not $BackupDirectory) { $BackupDirectory = Join-Path $ProjectRoot "backups" }
New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupName = "tenderpulse-$stamp.dump"
$containerPath = "/tmp/$backupName"
$backupPath = Join-Path $BackupDirectory $backupName
$containerId = (docker compose ps -q postgres).Trim()
if (-not $containerId) { throw "PostgreSQL container is not running." }

try {
    docker compose exec -T postgres sh -c "pg_dump -U `"`$POSTGRES_USER`" -d `"`$POSTGRES_DB`" -Fc -f `"$containerPath`""
    if ($LASTEXITCODE -ne 0) { throw "pg_dump failed." }
    docker cp "${containerId}:$containerPath" $backupPath
    if ($LASTEXITCODE -ne 0) { throw "Could not copy backup from the PostgreSQL container." }
} finally {
    docker compose exec -T postgres rm -f $containerPath | Out-Null
}

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $backupPath).Hash.ToLower()
[pscustomobject]@{ file = $backupName; sha256 = $hash; created_at = (Get-Date).ToUniversalTime().ToString("o") } |
    ConvertTo-Json | Set-Content -Encoding utf8 "${backupPath}.json"

$cutoff = (Get-Date).AddDays(-[math]::Abs($RetentionDays))
Get-ChildItem -LiteralPath $BackupDirectory -File -Filter "tenderpulse-*.dump*" |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force

Write-Host "Backup created: $backupPath"
