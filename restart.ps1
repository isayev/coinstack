# CoinStack - Restart Frontend & Backend
# 
# FIXED PORTS (DO NOT CHANGE):
#   Backend:  8000
#   Frontend: 3000
#
# Run: .\restart.ps1

Write-Host "`n=== CoinStack Server Restart ===" -ForegroundColor Cyan
Write-Host "Backend: 8000 | Frontend: 3000" -ForegroundColor Gray

# Step 1: Kill ALL processes on our ports
Write-Host "`n[1/4] Killing processes on ports 8000 and 3000..." -ForegroundColor Yellow

# Kill by port - more aggressive approach
$portsToKill = @(8000, 3000)
foreach ($port in $portsToKill) {
    $netstat = netstat -ano | Select-String ":$port\s" 
    foreach ($line in $netstat) {
        if ($line -match '\s(\d+)\s*$') {
            $processId = $matches[1]
            if ($processId -gt 0) {
                taskkill /F /PID $processId 2>$null | Out-Null
            }
        }
    }
}

# Also kill any python/node that might be hanging
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "    Waiting for ports to free up..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Verify ports are free
$port8000Free = $null -eq (netstat -ano | Select-String "LISTENING" | Select-String ":8000\s")
$port3000Free = $null -eq (netstat -ano | Select-String "LISTENING" | Select-String ":3000\s")

if (-not $port8000Free) {
    Write-Host "    WARNING: Port 8000 still in use!" -ForegroundColor Red
}
if (-not $port3000Free) {
    Write-Host "    WARNING: Port 3000 still in use!" -ForegroundColor Red
}

# Step 2: Start Backend on port 8000
Write-Host "[2/4] Starting backend on port 8000..." -ForegroundColor Yellow
$backendPath = Join-Path $PSScriptRoot "backend"
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000" -WorkingDirectory $backendPath -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 4

# Verify backend
$backendUp = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendUp = $true
            Write-Host "    Backend running on http://localhost:8000" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $backendUp) {
    Write-Host "    Backend failed to start on port 8000!" -ForegroundColor Red
    Write-Host "    Check if port 8000 is available" -ForegroundColor Red
    exit 1
}

# Step 3: Start Frontend on port 3000
Write-Host "[3/4] Starting frontend on port 3000..." -ForegroundColor Yellow
$frontendPath = Join-Path $PSScriptRoot "frontend"
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $frontendPath -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 4

# Verify frontend
$frontendUp = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $frontendUp = $true
            Write-Host "    Frontend running on http://localhost:3000" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $frontendUp) {
    Write-Host "    Frontend may still be starting..." -ForegroundColor Yellow
}

# Step 4: Summary
Write-Host "`n[4/4] Server Status:" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend API:  " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Frontend:     " -NoNewline  
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Quick Links:" -ForegroundColor Gray
Write-Host "    Collection: http://localhost:3000/"
Write-Host "    Audit:      http://localhost:3000/audit"
Write-Host "    API Health: http://localhost:8000/api/health"
Write-Host ""
Write-Host "Servers are running in background. Press any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
