@echo off
cd /d "%~dp0frontend"
title RealEstate Frontend :5173
call npm run dev -- --host 0.0.0.0 --port 5173
echo.
echo Frontend stopped.
pause
