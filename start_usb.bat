@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0venv\Scripts\python.exe" (
    echo ERROR: Run INSTALL_USB.BAT first.
    pause
    exit /b 1
)

if not exist "%~dp0frontend\node_modules" (
    echo ERROR: Run INSTALL_USB.BAT first (npm).
    pause
    exit /b 1
)

"%~dp0venv\Scripts\python.exe" -c "import django" 1>nul 2>&1
if errorlevel 1 (
    echo ERROR: Run INSTALL_USB.BAT first (django).
    pause
    exit /b 1
)

echo Starting BACKEND :8000 ...
start "RealEstate-Backend" "%~dp0_run_backend_usb.bat"

echo Starting FRONTEND :5173 ...
start "RealEstate-Frontend" "%~dp0_run_frontend_usb.bat"

echo.
echo Two windows started. Open: http://localhost:5173
echo.
pause
endlocal
exit /b 0
