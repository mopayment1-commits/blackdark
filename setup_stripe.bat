@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo BLACKDARK — Stripe setup
python scripts\setup_stripe.py
pause
