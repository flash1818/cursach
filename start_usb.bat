@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
  echo ERROR: Run install_usb.bat first (no venv folder).
  pause
  exit /b 1
)

venv\Scripts\python.exe -c "import django" 1>nul 2>nul
if errorlevel 1 (
  echo ERROR: Django missing. Run install_usb.bat
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo ERROR: Run install_usb.bat (no frontend\node_modules).
  pause
  exit /b 1
)

echo Starting backend http://localhost:8000
start "Django" cmd /k call "%~dp0_run_backend_usb.bat"

echo Starting frontend http://localhost:5173
start "Vite" cmd /k call "%~dp0_run_frontend_usb.bat"

echo.
echo Two windows opened. Open browser: http://localhost:5173
echo.
pause
endlocal
