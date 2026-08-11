@echo off
REM Open Soft Launch env in Notepad. Regenerates if missing/empty.
cd /d "%~dp0.."
python scripts\open_softlaunch_env.py --admin-email mopayment1@gmail.com %*
if errorlevel 1 (
  echo Failed to open Soft Launch env.
  exit /b 1
)
