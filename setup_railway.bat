@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo BLACKDARK — Railway production variables generator
python scripts\setup_production_env.py
pause
