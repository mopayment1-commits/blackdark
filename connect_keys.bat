@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title BLACKDARK - ربط المفاتيح
echo.
python scripts\auto_connect_keys.py
echo.
pause
