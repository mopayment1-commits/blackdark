@echo off
REM Open Soft Launch secrets in Notepad (Windows).
REM Double-click this file, or run from Command Prompt.

cd /d "%~dp0\.."

if not exist ".env.softlaunch.local" (
  echo File not found. Creating it now...
  python scripts\bootstrap_free_human_ops.py --admin-email mopayment1@gmail.com
)

if not exist ".env.softlaunch.local" (
  echo ERROR: could not create .env.softlaunch.local
  pause
  exit /b 1
)

echo Opening .env.softlaunch.local in Notepad...
echo Do NOT paste secrets into chat or email.
notepad ".env.softlaunch.local"
