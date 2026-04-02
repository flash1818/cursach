@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo === Real Estate Pro - install (USB / local PC) ===
echo Folder: %cd%
echo.

where python 1>nul 2>nul
if errorlevel 1 (
  echo ERROR: Python not in PATH. Install from python.org - enable Add to PATH.
  pause
  exit /b 1
)

where node 1>nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js not in PATH. Install LTS from nodejs.org
  pause
  exit /b 1
)

echo Step 1 - versions:
python --version
node -v
npm -v
echo.

if not exist "venv\Scripts\python.exe" (
  echo Step 2 - creating venv...
  python -m venv venv
  if errorlevel 1 (
    echo ERROR: venv failed. Try: py -3.12 -m venv venv
    pause
    exit /b 1
  )
) else (
  echo Step 2 - venv exists, skip create.
)

echo Step 3 - pip install...
call "%~dp0venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install --default-timeout=120 -r requirements.txt
if errorlevel 1 (
  echo ERROR: pip install failed. Check internet.
  pause
  exit /b 1
)

echo Step 4 - npm install...
pushd "%~dp0frontend"
call npm install
if errorlevel 1 (
  echo ERROR: npm install failed.
  popd
  pause
  exit /b 1
)
popd

cd /d "%~dp0"
echo Step 5 - migrate...
call "%~dp0venv\Scripts\activate.bat"
python manage.py migrate
if errorlevel 1 (
  echo ERROR: migrate failed.
  pause
  exit /b 1
)

echo Step 6 - seed demo data...
python seed_demo.py
if errorlevel 1 (
  echo WARNING: seed_demo failed, you can run it later manually.
)

echo.
echo ========================================
echo DONE. Next: double-click start_usb.bat
echo Site: http://localhost:5173
echo ========================================
echo.
pause
endlocal
exit /b 0
