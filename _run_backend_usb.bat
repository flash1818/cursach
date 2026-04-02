@echo off
cd /d "%~dp0"
set USE_POSTGRES=0
"%~dp0venv\Scripts\python.exe" -u manage.py runserver 0.0.0.0:8000
