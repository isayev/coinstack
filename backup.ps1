<#
.SYNOPSIS
    CoinStack V2 Full Backup Script - Creates versioned backups of database, images, and settings.

.DESCRIPTION
    Creates complete application state backups for V2 architecture including:
    - SQLite database (coinstack_v2.db)
    - Coin images (coin_images, cng_images, biddr_images, ebay_images)
    - LLM data (cache, costs, vision cache)
    - Settings (.env configuration)
    - User uploads
    
    Maintains 5 rolling backup versions with automatic rotation.

.PARAMETER Action
    backup  - Create a new backup (default)
    restore - Restore from a specific backup
    list    - List available backups

.PARAMETER Version
    For restore: Specify which backup version to restore (e.g., "20260124_153000")

.EXAMPLE
    .\backup.ps1
    Creates a new backup with automatic version rotation.

.EXAMPLE
    .\backup.ps1 -Action list
    Lists all available backup versions.

.EXAMPLE
    .\backup.ps1 -Action restore -Version "20260124_153000"
    Restores from the specified backup version.
#>

param(
    [ValidateSet("backup", "restore", "list")]
    [string]$Action = "backup",
    
    [string]$Version = ""
)

# Configuration
$ErrorActionPreference = "Stop"
$Script:ProjectRoot = $PSScriptRoot
$Script:BackendDir = Join-Path $ProjectRoot "backend"
$Script:DataDir = Join-Path $BackendDir "data"
$Script:RootDataDir = Join-Path $ProjectRoot "data"
$Script:BackupsDir = Join-Path $Script:BackendDir "backups"
$Script:MaxVersions = 10

# Paths to backup
$Script:DatabasePath = Join-Path $Script:BackendDir "coinstack_v2.db"
$Script:UploadsDir = Join-Path $BackendDir "uploads"
$Script:EnvFile = Join-Path $BackendDir ".env"

# Image directories in backend/data
$Script:ImageDirs = @("coin_images", "cng_images", "biddr_images", "ebay_images")

# LLM data files in root/data
$Script:LlmFiles = @("llm_cache.sqlite", "llm_costs.sqlite", "llm_vision_cache.sqlite")

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $color = switch ($Type) {
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        default { "Cyan" }
    }
    
    $prefix = switch ($Type) {
        "Success" { "[OK]" }
        "Warning" { "[WARN]" }
        "Error" { "[ERROR]" }
        default { "[INFO]" }
    }
    
    Write-Host "$prefix $Message" -ForegroundColor $color
}

function Get-BackupVersions {
    if (-not (Test-Path $BackupsDir)) {
        return @()
    }
    
    Get-ChildItem -Path $BackupsDir -Directory | 
        Where-Object { $_.Name -match '^\d{8}_{1}\d{6}$' } |
        Sort-Object Name -Descending |
        Select-Object -ExpandProperty Name
}

function Get-BackupManifest {
    param([string]$BackupVersion)
    
    $versionPath = Join-Path $BackupsDir $BackupVersion
    $manifestPath = Join-Path $versionPath "manifest.json"
    if (Test-Path $manifestPath) {
        return Get-Content $manifestPath | ConvertFrom-Json
    }
    return $null
}

function New-BackupVersion {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $BackupsDir $timestamp
    
    Write-Status "Creating V2 backup version: $timestamp"
    Write-Status "Backup location: $backupPath"
    
    # Ensure backup directory exists
    if (-not (Test-Path $BackupsDir)) {
        New-Item -ItemType Directory -Path $BackupsDir -Force | Out-Null
        Write-Status "Created backups directory"
    }
    
    # Create version directory
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    
    # Initialize manifest
    $manifest = @{
        version = $timestamp
        app_version = "V2.1"
        created_at = (Get-Date).ToString("o")
        components = @{}
        stats = @{
            total_files = 0
            total_size_mb = 0
        }
    }
    
    # 1. Backup Database (V2)
    Write-Status "Backing up V2 database..."
    if (Test-Path $DatabasePath) {
        $dbBackupPath = Join-Path $backupPath "coinstack_v2.db"
        Copy-Item -Path $DatabasePath -Destination $dbBackupPath -Force
        $dbSize = (Get-Item $dbBackupPath).Length
        $manifest.components["database"] = @{
            file = "coinstack_v2.db"
            size_bytes = $dbSize
            original_path = $DatabasePath
        }
        $manifest.stats.total_files++
        $manifest.stats.total_size_mb += [math]::Round($dbSize / 1MB, 2)
        Write-Status "Database backed up ($([math]::Round($dbSize / 1MB, 2)) MB)" "Success"
    } else {
        Write-Status "Database not found at $DatabasePath - skipping" "Warning"
        $manifest.components["database"] = @{ status = "not_found" }
    }
    
    # 2. Backup Settings (.env)
    Write-Status "Backing up settings..."
    if (Test-Path $EnvFile) {
        $envBackupPath = Join-Path $backupPath "settings"
        New-Item -ItemType Directory -Path $envBackupPath -Force | Out-Null
        Copy-Item -Path $EnvFile -Destination (Join-Path $envBackupPath ".env") -Force
        $envSize = (Get-Item $EnvFile).Length
        $manifest.components["settings"] = @{
            file = "settings/.env"
            size_bytes = $envSize
            original_path = $EnvFile
        }
        $manifest.stats.total_files++
        Write-Status "Settings backed up" "Success"
    }
    
    # 3. Backup Images
    Write-Status "Backing up image repositories..."
    $imagesBackupPath = Join-Path $backupPath "images"
    New-Item -ItemType Directory -Path $imagesBackupPath -Force | Out-Null
    
    foreach ($dirName in $ImageDirs) {
        $sourceDir = Join-Path $DataDir $dirName
        if (Test-Path $sourceDir) {
            $destDir = Join-Path $imagesBackupPath $dirName
            Copy-Item -Path $sourceDir -Destination $destDir -Recurse -Force
            $files = Get-ChildItem -Path $destDir -File -Recurse -ErrorAction SilentlyContinue
            $count = ($files | Measure-Object).Count
            $size = ($files | Measure-Object -Property Length -Sum).Sum
            if ($null -eq $size) { $size = 0 }
            
            $manifest.components[$dirName] = @{
                directory = "images/$dirName"
                file_count = $count
                size_bytes = $size
                original_path = $sourceDir
            }
            $manifest.stats.total_files += $count
            $manifest.stats.total_size_mb += [math]::Round($size / 1MB, 2)
            Write-Status "  - ${dirName}: $count files ($([math]::Round($size / 1MB, 2)) MB)" "Success"
        }
    }
    
    # 4. Backup LLM Data
    Write-Status "Backing up LLM caches and metrics..."
    $llmBackupPath = Join-Path $backupPath "llm_data"
    New-Item -ItemType Directory -Path $llmBackupPath -Force | Out-Null
    
    foreach ($fileName in $LlmFiles) {
        $sourceFile = Join-Path $RootDataDir $fileName
        if (Test-Path $sourceFile) {
            Copy-Item -Path $sourceFile -Destination $llmBackupPath -Force
            $size = (Get-Item $sourceFile).Length
            $manifest.components[$fileName] = @{
                file = "llm_data/$fileName"
                size_bytes = $size
                original_path = $sourceFile
            }
            $manifest.stats.total_files++
            $manifest.stats.total_size_mb += [math]::Round($size / 1MB, 2)
            Write-Status "  - $fileName backed up" "Success"
        }
    }
    
    # Write manifest
    $manifestPath = Join-Path $backupPath "manifest.json"
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -Path $manifestPath -Encoding UTF8
    
    # Recalculate total size
    $totalBackupSize = (Get-ChildItem -Path $backupPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
    $manifest.stats.total_size_mb = [math]::Round($totalBackupSize / 1MB, 2)
    
    Write-Host ""
    Write-Status "Backup completed successfully!" "Success"
    Write-Host "  Version:     $timestamp"
    Write-Host "  Total files: $($manifest.stats.total_files)"
    Write-Host "  Total size:  $($manifest.stats.total_size_mb) MB"
    Write-Host "  Location:    $backupPath"
    Write-Host ""
    
    Remove-OldBackups
    return $timestamp
}

function Remove-OldBackups {
    $versions = Get-BackupVersions
    if ($versions.Count -gt $MaxVersions) {
        $toRemove = $versions | Select-Object -Skip $MaxVersions
        Write-Status "Rotating old backups (keeping $MaxVersions most recent)..."
        foreach ($version in $toRemove) {
            $versionPath = Join-Path $BackupsDir $version
            Remove-Item -Path $versionPath -Recurse -Force
            Write-Status "Removed old backup: $version" "Warning"
        }
    }
}

function Show-BackupList {
    $versions = Get-BackupVersions
    if ($versions.Count -eq 0) {
        Write-Status "No backups found in $BackupsDir" "Warning"
        return
    }
    
    Write-Host ""
    Write-Host "Available Backup Versions (V2):" -ForegroundColor Cyan
    Write-Host "=" * 80
    
    foreach ($version in $versions) {
        $manifest = Get-BackupManifest -BackupVersion $version
        if ($manifest) {
            $created = [DateTime]::Parse($manifest.created_at).ToString("yyyy-MM-dd HH:mm:ss")
            Write-Host ""
            Write-Host "  Version: $version" -ForegroundColor Yellow
            Write-Host "    Created:     $created"
            Write-Host "    Total size:  $($manifest.stats.total_size_mb) MB"
            Write-Host "    App Version: $($manifest.app_version)"
        }
    }
    Write-Host ""
}

function Restore-BackupVersion {
    param([string]$BackupVersion)
    
    if ([string]::IsNullOrWhiteSpace($BackupVersion)) {
        Write-Status "Please specify a version to restore using -Version parameter" "Error"
        return
    }
    
    $versionPath = Join-Path $BackupsDir $BackupVersion
    if (-not (Test-Path $versionPath)) {
        Write-Status "Backup version '$BackupVersion' not found" "Error"
        return
    }
    
    $manifest = Get-BackupManifest -BackupVersion $BackupVersion
    if (-not $manifest) {
        Write-Status "Manifest not found for backup '$BackupVersion'" "Error"
        return
    }
    
    Write-Host ""
    Write-Status "Restoring from V2 backup: $BackupVersion"
    Write-Host "WARNING: This will overwrite current V2 data!" -ForegroundColor Red
    $confirm = Read-Host "Type 'RESTORE' to confirm"
    if ($confirm -ne "RESTORE") {
        Write-Status "Restore cancelled" "Warning"
        return
    }
    
    # 1. Restore Database
    if ($manifest.components.database) {
        Write-Status "Restoring coinstack_v2.db..."
        Copy-Item -Path (Join-Path $versionPath "coinstack_v2.db") -Destination $DatabasePath -Force
    }
    
    # 2. Restore Images
    foreach ($dirName in $ImageDirs) {
        $src = Join-Path $versionPath "images/$dirName"
        if (Test-Path $src) {
            Write-Status "Restoring $dirName..."
            $dest = Join-Path $DataDir $dirName
            if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force }
            Copy-Item -Path $src -Destination $dest -Recurse -Force
        }
    }
    
    # 3. Restore LLM Data
    foreach ($fileName in $LlmFiles) {
        $src = Join-Path $versionPath "llm_data/$fileName"
        if (Test-Path $src) {
            Write-Status "Restoring $fileName..."
            Copy-Item -Path $src -Destination (Join-Path $RootDataDir $fileName) -Force
        }
    }
    
    # 4. Restore Settings
    $envSrc = Join-Path $versionPath "settings/.env"
    if (Test-Path $envSrc) {
        Write-Status "Restoring .env..."
        Copy-Item -Path $envSrc -Destination $EnvFile -Force
    }
    
    Write-Status "Restore completed successfully!" "Success"
}

# Main execution
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CoinStack V2 Backup Utility" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

switch ($Action) {
    "backup" { New-BackupVersion }
    "restore" { Restore-BackupVersion -BackupVersion $Version }
    "list" { Show-BackupList }
}