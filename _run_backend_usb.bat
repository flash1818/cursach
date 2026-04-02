@echo off
cd /d "%~dp0"
set USE_POSTGRES=0
set PGCLIENTENCODING=UTF8
title RealEstate Backend :8000
"%~dp0venv\Scripts\python.exe" -u "%~dp0manage.py" runserver 0.0.0.0:8000
echo.
echo Backend stopped.
pause
