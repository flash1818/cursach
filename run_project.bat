@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0venv\Scripts\python.exe" (
    echo ERROR: No venv. Double-click INSTALL_USB.BAT first.
    pause
    exit /b 1
)

if not exist "%~dp0frontend\node_modules" (
    echo ERROR: No frontend\node_modules. Double-click INSTALL_USB.BAT first.
    pause
    exit /b 1
)

"%~dp0venv\Scripts\python.exe" -c "import django" 1>nul 2>&1
if errorlevel 1 (
    echo Django missing - installing from requirements.txt ...
    echo Need internet for pip. Wait...
    "%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
    "%~dp0venv\Scripts\python.exe" -m pip install --default-timeout=120 -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo ERROR: pip failed. Run INSTALL_USB.BAT or check internet.
        pause
        exit /b 1
    )
    "%~dp0venv\Scripts\python.exe" -c "import django" 1>nul 2>&1
    if errorlevel 1 (
        echo ERROR: Django still missing after pip. Run INSTALL_USB.BAT.
        pause
        exit /b 1
    )
    echo OK - Django installed.
    echo.
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
