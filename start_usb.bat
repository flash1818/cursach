@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM Запуск backend + frontend (после install_usb.bat). SQLite по умолчанию.

set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist "venv\Scripts\python.exe" (
  echo Сначала выполните install_usb.bat — нет папки venv.
  pause
  exit /b 1
)

venv\Scripts\python.exe -c "import django" >nul 2>nul
if errorlevel 1 (
  echo Django не установлен. Запустите install_usb.bat
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo Нет frontend\node_modules. Запустите install_usb.bat
  pause
  exit /b 1
)

set USE_POSTGRES=0
set PGCLIENTENCODING=UTF8

echo [1/2] Backend: http://localhost:8000
start "Django" cmd /k pushd "%ROOT%" ^&^& venv\Scripts\python.exe -u manage.py runserver 0.0.0.0:8000

echo [2/2] Frontend: http://localhost:5173
start "Vite" cmd /k pushd "%ROOT%frontend" ^&^& npm run dev -- --host 0.0.0.0 --port 5173

echo.
echo Окна серверов открыты. Это окно можно закрыть.
echo Браузер: http://localhost:5173
echo.
pause
endlocal
