<#
.SYNOPSIS
    CoinStack Full Backup Script - Creates versioned backups of database, images, and settings.

.DESCRIPTION
    Creates complete application state backups including:
    - SQLite database (coinstack.db)
    - Coin images (coin_images, cng_images directories)
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
$Script:BackupsDir = Join-Path $BackendDir "backups"
$Script:MaxVersions = 5

# Paths to backup
$Script:DatabasePath = Join-Path $DataDir "coinstack.db"
$Script:CoinImagesDir = Join-Path $DataDir "coin_images"
$Script:CngImagesDir = Join-Path $DataDir "cng_images"
$Script:UploadsDir = Join-Path $BackendDir "uploads"
$Script:EnvFile = Join-Path $BackendDir ".env"

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
    <#
    .SYNOPSIS
        Returns list of existing backup versions sorted by date (newest first).
    #>
    if (-not (Test-Path $BackupsDir)) {
        return @()
    }
    
    Get-ChildItem -Path $BackupsDir -Directory | 
        Where-Object { $_.Name -match '^\d{8}_\d{6}$' } |
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
    <#
    .SYNOPSIS
        Creates a new timestamped backup of the entire application state.
    #>
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $BackupsDir $timestamp
    
    Write-Status "Creating backup version: $timestamp"
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
        created_at = (Get-Date).ToString("o")
        components = @{}
        stats = @{
            total_files = 0
            total_size_mb = 0
        }
    }
    
    # 1. Backup Database
    Write-Status "Backing up database..."
    if (Test-Path $DatabasePath) {
        $dbBackupPath = Join-Path $backupPath "coinstack.db"
        Copy-Item -Path $DatabasePath -Destination $dbBackupPath -Force
        $dbSize = (Get-Item $dbBackupPath).Length
        $manifest.components["database"] = @{
            file = "coinstack.db"
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
    } else {
        Write-Status ".env file not found - skipping" "Warning"
        $manifest.components["settings"] = @{ status = "not_found" }
    }
    
    # 3. Backup Coin Images
    Write-Status "Backing up coin images..."
    $imagesBackupPath = Join-Path $backupPath "images"
    New-Item -ItemType Directory -Path $imagesBackupPath -Force | Out-Null
    
    # Coin images
    if (Test-Path $CoinImagesDir) {
        $coinImagesBackup = Join-Path $imagesBackupPath "coin_images"
        Copy-Item -Path $CoinImagesDir -Destination $coinImagesBackup -Recurse -Force
        $coinImageFiles = Get-ChildItem -Path $coinImagesBackup -File -Recurse
        $coinImageCount = ($coinImageFiles | Measure-Object).Count
        $coinImageSize = ($coinImageFiles | Measure-Object -Property Length -Sum).Sum
        $manifest.components["coin_images"] = @{
            directory = "images/coin_images"
            file_count = $coinImageCount
            size_bytes = $coinImageSize
            original_path = $CoinImagesDir
        }
        $manifest.stats.total_files += $coinImageCount
        $manifest.stats.total_size_mb += [math]::Round($coinImageSize / 1MB, 2)
        Write-Status "Coin images backed up ($coinImageCount files, $([math]::Round($coinImageSize / 1MB, 2)) MB)" "Success"
    } else {
        Write-Status "coin_images directory not found - skipping" "Warning"
        $manifest.components["coin_images"] = @{ status = "not_found" }
    }
    
    # CNG images (scraped)
    if (Test-Path $CngImagesDir) {
        $cngImagesBackup = Join-Path $imagesBackupPath "cng_images"
        Copy-Item -Path $CngImagesDir -Destination $cngImagesBackup -Recurse -Force
        $cngImageFiles = Get-ChildItem -Path $cngImagesBackup -File -Recurse
        $cngImageCount = ($cngImageFiles | Measure-Object).Count
        $cngImageSize = ($cngImageFiles | Measure-Object -Property Length -Sum).Sum
        $manifest.components["cng_images"] = @{
            directory = "images/cng_images"
            file_count = $cngImageCount
            size_bytes = $cngImageSize
            original_path = $CngImagesDir
        }
        $manifest.stats.total_files += $cngImageCount
        $manifest.stats.total_size_mb += [math]::Round($cngImageSize / 1MB, 2)
        Write-Status "CNG images backed up ($cngImageCount files, $([math]::Round($cngImageSize / 1MB, 2)) MB)" "Success"
    } else {
        Write-Status "cng_images directory not found - skipping" "Warning"
        $manifest.components["cng_images"] = @{ status = "not_found" }
    }
    
    # 4. Backup Uploads
    Write-Status "Backing up uploads..."
    if (Test-Path $UploadsDir) {
        $uploadsBackupPath = Join-Path $backupPath "uploads"
        Copy-Item -Path $UploadsDir -Destination $uploadsBackupPath -Recurse -Force
        $uploadFiles = Get-ChildItem -Path $uploadsBackupPath -File -Recurse -ErrorAction SilentlyContinue
        $uploadCount = ($uploadFiles | Measure-Object).Count
        $uploadSize = ($uploadFiles | Measure-Object -Property Length -Sum).Sum
        if ($null -eq $uploadSize) { $uploadSize = 0 }
        $manifest.components["uploads"] = @{
            directory = "uploads"
            file_count = $uploadCount
            size_bytes = $uploadSize
            original_path = $UploadsDir
        }
        $manifest.stats.total_files += $uploadCount
        $manifest.stats.total_size_mb += [math]::Round($uploadSize / 1MB, 2)
        Write-Status "Uploads backed up ($uploadCount files)" "Success"
    } else {
        Write-Status "uploads directory not found - skipping" "Warning"
        $manifest.components["uploads"] = @{ status = "not_found" }
    }
    
    # Write manifest
    $manifestPath = Join-Path $backupPath "manifest.json"
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -Path $manifestPath -Encoding UTF8
    Write-Status "Manifest created"
    
    # Calculate total backup size
    $totalBackupSize = (Get-ChildItem -Path $backupPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
    $manifest.stats.total_size_mb = [math]::Round($totalBackupSize / 1MB, 2)
    
    Write-Host ""
    Write-Status "Backup completed successfully!" "Success"
    Write-Host "  Version:     $timestamp"
    Write-Host "  Total files: $($manifest.stats.total_files)"
    Write-Host "  Total size:  $($manifest.stats.total_size_mb) MB"
    Write-Host "  Location:    $backupPath"
    Write-Host ""
    
    # Rotate old backups
    Remove-OldBackups
    
    return $timestamp
}

function Remove-OldBackups {
    <#
    .SYNOPSIS
        Removes old backups keeping only the most recent MaxVersions.
    #>
    
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
    <#
    .SYNOPSIS
        Displays list of available backup versions with details.
    #>
    
    $versions = Get-BackupVersions
    
    if ($versions.Count -eq 0) {
        Write-Status "No backups found in $BackupsDir" "Warning"
        return
    }
    
    Write-Host ""
    Write-Host "Available Backup Versions:" -ForegroundColor Cyan
    Write-Host "=" * 80
    
    foreach ($version in $versions) {
        $manifest = Get-BackupManifest -BackupVersion $version
        $versionPath = Join-Path $BackupsDir $version
        
        if ($manifest) {
            $created = [DateTime]::Parse($manifest.created_at).ToString("yyyy-MM-dd HH:mm:ss")
            $size = $manifest.stats.total_size_mb
            $files = $manifest.stats.total_files
            
            Write-Host ""
            Write-Host "  Version: $version" -ForegroundColor Yellow
            Write-Host "    Created:     $created"
            Write-Host "    Total size:  $size MB"
            Write-Host "    Total files: $files"
            
            # Component status
            Write-Host "    Components:"
            $compNames = @("database", "settings", "coin_images", "cng_images", "uploads")
            foreach ($comp in $compNames) {
                $compData = $manifest.components.$comp
                if ($null -eq $compData -or $compData.status -eq "not_found") {
                    Write-Host "      - $comp : [not included]" -ForegroundColor DarkGray
                } else {
                    $compInfo = if ($compData.file_count) {
                        "$($compData.file_count) files"
                    } elseif ($compData.size_bytes) {
                        "$([math]::Round($compData.size_bytes / 1KB, 1)) KB"
                    } else {
                        "included"
                    }
                    Write-Host "      - $comp : $compInfo" -ForegroundColor Green
                }
            }
        } else {
            Write-Host ""
            Write-Host "  Version: $version" -ForegroundColor Yellow
            Write-Host "    [Manifest not found - backup may be corrupted]" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "=" * 80
    Write-Host "To restore: .\backup.ps1 -Action restore -Version `"VERSION`"" -ForegroundColor Cyan
    Write-Host ""
}

function Restore-BackupVersion {
    param([string]$BackupVersion)
    
    <#
    .SYNOPSIS
        Restores application state from a specific backup version.
    #>
    
    if ([string]::IsNullOrWhiteSpace($BackupVersion)) {
        Write-Status "Please specify a version to restore using -Version parameter" "Error"
        Write-Status "Use -Action list to see available versions"
        return
    }
    
    $versionPath = Join-Path $BackupsDir $BackupVersion
    
    if (-not (Test-Path $versionPath)) {
        Write-Status "Backup version '$BackupVersion' not found" "Error"
        Write-Status "Use -Action list to see available versions"
        return
    }
    
    $manifest = Get-BackupManifest -BackupVersion $BackupVersion
    
    if (-not $manifest) {
        Write-Status "Manifest not found for backup '$BackupVersion'" "Error"
        return
    }
    
    Write-Host ""
    Write-Status "Restoring from backup: $BackupVersion"
    Write-Status "Created: $($manifest.created_at)"
    Write-Host ""
    
    # Confirm restore
    Write-Host "WARNING: This will overwrite current data!" -ForegroundColor Red
    Write-Host "Components to restore:"
    foreach ($comp in $manifest.components.Keys) {
        $compData = $manifest.components[$comp]
        if ($compData.status -ne "not_found") {
            Write-Host "  - $comp"
        }
    }
    Write-Host ""
    
    $confirm = Read-Host "Type 'RESTORE' to confirm"
    if ($confirm -ne "RESTORE") {
        Write-Status "Restore cancelled" "Warning"
        return
    }
    
    Write-Host ""
    
    # Create pre-restore backup
    Write-Status "Creating pre-restore safety backup..."
    $safetyBackup = New-BackupVersion
    Write-Status "Safety backup created: $safetyBackup" "Success"
    Write-Host ""
    
    # Restore Database
    if ($manifest.components["database"] -and $manifest.components["database"].status -ne "not_found") {
        Write-Status "Restoring database..."
        $dbSource = Join-Path $versionPath "coinstack.db"
        if (Test-Path $dbSource) {
            # Ensure data directory exists
            $dataDir = Split-Path $DatabasePath -Parent
            if (-not (Test-Path $dataDir)) {
                New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
            }
            Copy-Item -Path $dbSource -Destination $DatabasePath -Force
            Write-Status "Database restored" "Success"
        }
    }
    
    # Restore Settings
    if ($manifest.components["settings"] -and $manifest.components["settings"].status -ne "not_found") {
        Write-Status "Restoring settings..."
        $settingsDir = Join-Path $versionPath "settings"
        $envSource = Join-Path $settingsDir ".env"
        if (Test-Path $envSource) {
            Copy-Item -Path $envSource -Destination $EnvFile -Force
            Write-Status "Settings restored" "Success"
        }
    }
    
    # Restore Coin Images
    if ($manifest.components["coin_images"] -and $manifest.components["coin_images"].status -ne "not_found") {
        Write-Status "Restoring coin images..."
        $imagesDir = Join-Path $versionPath "images"
        $coinImgSource = Join-Path $imagesDir "coin_images"
        if (Test-Path $coinImgSource) {
            if (Test-Path $CoinImagesDir) {
                Remove-Item -Path $CoinImagesDir -Recurse -Force
            }
            Copy-Item -Path $coinImgSource -Destination $CoinImagesDir -Recurse -Force
            Write-Status "Coin images restored" "Success"
        }
    }
    
    # Restore CNG Images
    if ($manifest.components["cng_images"] -and $manifest.components["cng_images"].status -ne "not_found") {
        Write-Status "Restoring CNG images..."
        $cngImgSource = Join-Path $imagesDir "cng_images"
        if (Test-Path $cngImgSource) {
            if (Test-Path $CngImagesDir) {
                Remove-Item -Path $CngImagesDir -Recurse -Force
            }
            Copy-Item -Path $cngImgSource -Destination $CngImagesDir -Recurse -Force
            Write-Status "CNG images restored" "Success"
        }
    }
    
    # Restore Uploads
    if ($manifest.components["uploads"] -and $manifest.components["uploads"].status -ne "not_found") {
        Write-Status "Restoring uploads..."
        $uploadsSource = Join-Path $versionPath "uploads"
        if (Test-Path $uploadsSource) {
            if (Test-Path $UploadsDir) {
                Remove-Item -Path $UploadsDir -Recurse -Force
            }
            Copy-Item -Path $uploadsSource -Destination $UploadsDir -Recurse -Force
            Write-Status "Uploads restored" "Success"
        }
    }
    
    Write-Host ""
    Write-Status "Restore completed successfully!" "Success"
    Write-Status "A safety backup was created: $safetyBackup"
    Write-Status "Please restart the application to apply changes."
    Write-Host ""
}

# Main execution
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CoinStack Backup Utility v1.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

switch ($Action) {
    "backup" {
        New-BackupVersion
    }
    "restore" {
        Restore-BackupVersion -BackupVersion $Version
    }
    "list" {
        Show-BackupList
    }
}
