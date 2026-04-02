@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%CD%"

if not exist "%ROOT%\venv\Scripts\python.exe" (
    echo ERROR: Run INSTALL.BAT first.
    pause
    exit /b 1
)

if not exist "%ROOT%\frontend\node_modules" (
    echo ERROR: Run INSTALL.BAT first (npm).
    pause
    exit /b 1
)

"%ROOT%\venv\Scripts\python.exe" -c "import django" 1>nul 2>&1
if errorlevel 1 (
    echo Django missing - pip install...
    "%ROOT%\venv\Scripts\python.exe" -m pip install --default-timeout=120 -r "%ROOT%\requirements.txt"
    if errorlevel 1 (
        echo ERROR: Run INSTALL.BAT
        pause
        exit /b 1
    )
)

echo Backend :8000
start "RealEstate-Backend" cmd /k cd /d "%ROOT%" ^&^& set USE_POSTGRES=0 ^&^& set PGCLIENTENCODING=UTF8 ^&^& "%ROOT%\venv\Scripts\python.exe" -u "%ROOT%\manage.py" runserver 0.0.0.0:8000

echo Frontend :5173
start "RealEstate-Frontend" cmd /k cd /d "%ROOT%\frontend" ^&^& npm run dev -- --host 0.0.0.0 --port 5173

echo.
echo Browser: http://localhost:5173
echo.
pause
endlocal
exit /b 0
