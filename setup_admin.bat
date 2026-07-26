@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo BLACKDARK — Admin setup
set /p EMAIL=Enter your admin email: 
python scripts\setup_admin.py %EMAIL%
echo.
echo Restart server: start_blackdark.bat
pause
