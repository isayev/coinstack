# CoinStack V2 Developer Start Script
# Usage: ./run_dev.ps1

Write-Host "starting coinstack v2 dev environment..." -ForegroundColor Cyan

# 1. Kill ports 8000 and 3000
Get-Process -Name "python", "node", "uvicorn" -ErrorAction SilentlyContinue | Where-Object { 
    $_.Path -match "coinstack" # Basic safety check, might not catch all
} 
# Harder kill by ports
$ports = 8000, 3000
foreach ($port in $ports) {
    echo "clearing port $port"
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns.OwningProcess | Select-Object -Unique
        foreach ($pid_ in $pids) {
            Stop-Process -Id $pid_ -Force -ErrorAction SilentlyContinue
        }
    }
}

Start-Sleep -Seconds 1

# 2. Start Backend (V2)
Write-Host "starting backend (v2)..." -ForegroundColor Yellow
$backendArgs = @("-m", "uvicorn", "src.infrastructure.web.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload")
Start-Process -FilePath "python" -ArgumentList $backendArgs -WorkingDirectory "$PSScriptRoot\backend" -WindowStyle Hidden

# 3. Start Frontend
Write-Host "starting frontend..." -ForegroundColor Yellow
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "$PSScriptRoot\frontend" -WindowStyle Hidden

Write-Host "done. backend: http://localhost:8000 | frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "use 'get-process | stop-process' or manually kill terminal to stop." -ForegroundColor Gray
