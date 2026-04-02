@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0venv\Scripts\python.exe" (
    echo ERROR: Run INSTALL_USB.BAT first.
    pause
    exit /b 1
)

if not exist "%~dp0frontend\node_modules" (
    echo ERROR: Run INSTALL_USB.BAT first - npm missing.
    pause
    exit /b 1
)

"%~dp0venv\Scripts\python.exe" -c "import django" 1>nul 2>&1
if errorlevel 1 (
    echo ERROR: Run INSTALL_USB.BAT first - django missing.
    pause
    exit /b 1
)

echo Starting backend :8000 ...
start "RealEstate-Backend" "%~dp0_run_backend_usb.bat"

echo Starting frontend :5173 ...
start "RealEstate-Frontend" "%~dp0_run_frontend_usb.bat"

echo.
echo Open in browser: http://localhost:5173
echo.
pause
endlocal
exit /b 0
