@echo off
REM CoinStack Backup Utility - Quick Launcher
REM Double-click this file to create a backup

echo.
echo CoinStack Backup Utility
echo ========================
echo.

cd /d "%~dp0"

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: PowerShell is required but not found.
    pause
    exit /b 1
)

REM Run the backup script
powershell -ExecutionPolicy Bypass -File "backup.ps1" %*

echo.
pause
