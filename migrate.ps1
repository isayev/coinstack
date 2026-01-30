# CoinStack Database Migration Script
# Enforces "Database Safety" Rule: Backup BEFORE Migration

$ErrorActionPreference = "Stop"

Write-Host "Starting Safe Migration Process..." -ForegroundColor Cyan

# 1. Define Paths
$DB_PATH = "backend\coinstack_v2.db"
$BACKUP_DIR = "backend\backups"

# 2. Check if DB exists (skip backup if fresh install)
if (Test-Path $DB_PATH) {
    # 3. Create Backup
    if (-not (Test-Path $BACKUP_DIR)) {
        New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "$BACKUP_DIR\coinstack_$timestamp.db"
    
    Write-Host "Creating backup at: $backupPath" -ForegroundColor Yellow
    Copy-Item $DB_PATH $backupPath
    Write-Host "Backup successful." -ForegroundColor Green

    # Cleanup old backups (keep 5 most recent)
    $backups = Get-ChildItem "$BACKUP_DIR\coinstack_*.db" | Sort-Object LastWriteTime -Descending
    if ($backups.Count -gt 5) {
        $backups | Select-Object -Skip 5 | Remove-Item
        Write-Host "Cleaned up $($backups.Count - 5) old backups." -ForegroundColor Gray
    }
} else {
    Write-Host "No existing database found. Skipping backup." -ForegroundColor Yellow
}

# 4. Run Migrations
Write-Host "Running Alembic migrations..." -ForegroundColor Cyan
Set-Location backend
try {
    uv run alembic upgrade head
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Migration complete." -ForegroundColor Green
    } else {
        Write-Error "Migration failed with exit code $LASTEXITCODE"
    }
} finally {
    Set-Location ..
}
