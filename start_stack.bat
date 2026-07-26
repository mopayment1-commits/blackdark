@echo off
chcp 65001 >nul
echo BLACKDARK — Microservices Stack (Postgres + Redis + Kafka + Vault)
echo.

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
)

findstr /C:"POSTGRES_PASSWORD=" .env | findstr /V "=$" >nul
if errorlevel 1 (
    echo POSTGRES_PASSWORD=blackdark_local_2026>> .env
    echo Added POSTGRES_PASSWORD to .env
)

echo Starting docker compose...
docker compose up -d --build

echo.
echo Web:    http://localhost:8080
echo Admin:  http://localhost:8080/admin/launch  (login as admin)
echo Vault:  http://localhost:8200  token=blackdark-dev-root
echo Kafka:  localhost:9092
echo.
pause
