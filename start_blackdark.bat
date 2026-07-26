@echo off
chcp 65001 >nul
cd /d "%~dp0"
title BLACKDARK
echo.
echo تشغيل BLACKDARK...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 " ^| findstr "LISTENING"') do (
    echo إيقاف عملية قديمة على المنفذ 8080 PID=%%a
    taskkill /PID %%a /F >nul 2>&1
)
python scripts\auto_connect_keys.py
echo.
python scripts\activate_100_exchanges.py
echo.
python scripts\activate_live_execution.py
echo.
python run_service.py all --port 8080
