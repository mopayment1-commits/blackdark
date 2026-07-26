@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo BLACKDARK — Launch Verify
python scripts\generate_pwa_icons.py
python scripts\launch_verify.py http://127.0.0.1:8080
pause
