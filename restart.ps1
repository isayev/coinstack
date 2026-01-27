# CoinStack V2 - Local Deployment Script
# 
# FIXED PORTS (MANDATORY):
#   Backend:  8000 (FastAPI)
#   Frontend: 3000 (Vite)
#
# Usage: .\restart.ps1

Write-Host "`n=== CoinStack V2 Local Deployment ===" -ForegroundColor Cyan
Write-Host "Backend: 8000 | Frontend: 3000" -ForegroundColor Gray

# 1. Kill processes on ports 8000 and 3000
Write-Host "`n[1/3] Clearing ports..." -ForegroundColor Yellow

function Kill-Port ($port) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $pid_to_kill = $conn.OwningProcess
            if ($pid_to_kill -gt 0) {
                Write-Host "    Killing PID $pid_to_kill on port $port" -ForegroundColor Gray
                Stop-Process -Id $pid_to_kill -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Kill-Port 8000
Kill-Port 3000

# Aggressive cleanup of python/node if ports stick
# Get-Process -Name uvicorn, python, node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

# 2. Start Backend (V2 Clean Architecture)
Write-Host "[2/3] Starting Backend (V2)..." -ForegroundColor Yellow
$backendPath = Join-Path $PSScriptRoot "backend"

# Detect Python (venv or global)
$pythonCmd = "python"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonCmd = $venvPython
    Write-Host "    Using venv: $pythonCmd" -ForegroundColor Cyan
}

# Note: We use run_server.py which sets Windows event loop policy for Playwright
$backendArgs = @("run_server.py")
Start-Process -FilePath $pythonCmd -ArgumentList $backendArgs -WorkingDirectory $backendPath -NoNewWindow

# Wait for backend to initialize
Write-Host "    Waiting for API..." -ForegroundColor Gray
$retries = 0
while ($retries -lt 10) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -Method Head -ErrorAction Stop -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "    Backend is UP!" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 1
        $retries++
    }
}

if ($retries -eq 10) {
    Write-Host "    Timeout waiting for backend. It might still be starting." -ForegroundColor Red
}

# 3. Start Frontend
Write-Host "[3/3] Starting Frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path $PSScriptRoot "frontend"
Start-Process -FilePath "npm" -ArgumentList "run", "dev", "--", "--port", "3000" -WorkingDirectory $frontendPath -NoNewWindow

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Frontend: " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend:  " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "API V2:   " -NoNewline; Write-Host "http://localhost:8000/api/v2/coins" -ForegroundColor Cyan