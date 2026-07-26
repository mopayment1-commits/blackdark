# Docker Compose verification (Buyer Requirement)
# Run after installing Docker Desktop: https://www.docker.com/products/docker-desktop/

param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== BLACKDARK Docker Verify ===" -ForegroundColor Cyan

# 1. Check Docker installed
try {
    $ver = docker --version
    Write-Host "[OK] Docker: $ver" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Docker Desktop not installed." -ForegroundColor Red
    Write-Host "Install: https://www.docker.com/products/docker-desktop/"
    Write-Host "After install, restart PC and re-run this script."
    exit 1
}

# 2. Check Docker daemon
try {
    docker info 2>$null | Out-Null
    Write-Host "[OK] Docker daemon running" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Docker daemon not running. Start Docker Desktop." -ForegroundColor Red
    exit 1
}

# 3. Validate compose file
docker compose config --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] docker-compose.yml valid" -ForegroundColor Green
} else {
    Write-Host "[FAIL] docker-compose.yml invalid" -ForegroundColor Red
    exit 1
}

# 4. Build and start
if (-not $SkipBuild) {
    Write-Host "Building images (may take 5-10 min first time)..." -ForegroundColor Yellow
    docker compose build
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

Write-Host "Starting stack..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) { exit 1 }

Start-Sleep -Seconds 25

# 5. Health checks
$checks = @(
    @{ Name="web sidecar"; Url="http://127.0.0.1:8180/health/live" },
    @{ Name="web ready"; Url="http://127.0.0.1:8080/health/ready" },
    @{ Name="redis"; Cmd="docker compose exec -T redis redis-cli ping" }
)

$allOk = $true
foreach ($c in $checks) {
    if ($c.Url) {
        try {
            $r = Invoke-WebRequest -Uri $c.Url -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) {
                Write-Host "[OK] $($c.Name)" -ForegroundColor Green
            } else { $allOk = $false }
        } catch {
            Write-Host "[FAIL] $($c.Name)" -ForegroundColor Red
            $allOk = $false
        }
    }
}

Write-Host ""
if ($allOk) {
    Write-Host "PASS — Docker Compose verified" -ForegroundColor Green
    Write-Host "  Web:     http://localhost:8080"
    Write-Host "  GraphQL: http://localhost:8080/graphql"
} else {
    Write-Host "PARTIAL — some checks failed. Run: docker compose logs web" -ForegroundColor Yellow
}
