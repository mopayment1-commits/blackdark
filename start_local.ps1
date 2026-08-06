# BLACKDARK — local Oracle (Windows). Double-click or: powershell -File start_local.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    Write-Host "Activate/create .venv first (python -m venv .venv), then run again."
    exit 1
}

# Soft local defaults (do not override if already set in .env / session)
if (-not $env:ENV) { $env:ENV = "development" }
if (-not $env:SOFT_LAUNCH) { $env:SOFT_LAUNCH = "true" }
if (-not $env:SERVICE_MODE) { $env:SERVICE_MODE = "web" }
if (-not $env:MANIFEST_AUTO_APPROVE) { $env:MANIFEST_AUTO_APPROVE = "true" }
if (-not $env:MANIFEST_REQUIRE_REVIEW) { $env:MANIFEST_REQUIRE_REVIEW = "false" }
if (-not $env:RUN_AGGREGATOR) { $env:RUN_AGGREGATOR = "false" }
if (-not $env:INGESTION_ENABLED) { $env:INGESTION_ENABLED = "false" }

Write-Host "Starting BLACKDARK Oracle at http://localhost:8080 ..."
& .\.venv\Scripts\python.exe run_service.py web
