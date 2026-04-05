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
    echo ERROR: Run INSTALL.BAT first - npm deps missing.
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

echo Backend 0.0.0.0 port 8000 (Daphne: HTTP + WebSocket)
start "RealEstate-Backend" /D "%ROOT%" cmd /k "set USE_POSTGRES=0&& set PGCLIENTENCODING=UTF8&& set DJANGO_SETTINGS_MODULE=realestate_site.settings&& venv\Scripts\daphne.exe -b 0.0.0.0 -p 8000 realestate_site.asgi:application"

echo Frontend 0.0.0.0 port 5173
start "RealEstate-Frontend" /D "%ROOT%\frontend" cmd /k "npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo Open in browser: localhost port 5173
echo You can close this window; servers stay in the other two windows.
echo.
pause
endlocal
exit /b 0
