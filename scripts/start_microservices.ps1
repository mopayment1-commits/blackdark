# BLACKDARK — Start microservices locally (Windows, no Docker required)
# Usage: .\scripts\start_microservices.ps1
# Stop:  Close the spawned PowerShell windows or Ctrl+C in each

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — edit keys as needed."
}

$env:SERVICE_BUS_LOCAL = "true"
$env:LOW_LATENCY_MODE = "true"
$env:EXCHANGE_WS_ENABLED = "true"

function Show-Worker($Mode, $Port) {
    $title = "BLACKDARK-$Mode"
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$Root'; `$env:SERVICE_MODE='$Mode'; python run_service.py $Mode --port $Port"
    ) -WindowStyle Normal
    Write-Output "Started $title on port $Port"
}

Show-Worker "web" 8080
Start-Sleep -Seconds 2
Show-Worker "aggregator" 8091
Show-Worker "arbitrage" 8092
Show-Worker "ingestion" 8093

Write-Host ""
Write-Host "Microservices starting..."
Write-Host "  Web UI:     http://localhost:8080/health/live"
Write-Host "  Aggregator: http://localhost:8091/health/live"
Write-Host "  Arbitrage:  http://localhost:8092/health/live"
Write-Host "  Ingestion:  http://localhost:8093/health/live"
Write-Host ""
Write-Host "For PostgreSQL + Redis, install Docker Desktop and run: docker compose up -d"
