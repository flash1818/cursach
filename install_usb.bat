@echo off
setlocal
cd /d "%~dp0"

echo.
echo ========================================
echo   Real Estate Pro - INSTALL
echo ========================================
echo   Folder: %CD%
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Add Python to PATH.
    pause
    exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found.
    pause
    exit /b 1
)

python --version
node -v
echo.

if exist "%~dp0venv\Scripts\python.exe" goto HAVE_VENV

echo Creating venv...
python -m venv "%~dp0venv"
if errorlevel 1 (
    echo ERROR: Cannot create venv.
    pause
    exit /b 1
)

:HAVE_VENV
echo Upgrading pip...
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: pip upgrade failed.
    pause
    exit /b 1
)

echo Installing requirements.txt ...
"%~dp0venv\Scripts\python.exe" -m pip install --default-timeout=120 -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo npm install in frontend ...
cd /d "%~dp0frontend"
if errorlevel 1 (
    echo ERROR: No frontend folder.
    pause
    exit /b 1
)
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed.
    cd /d "%~dp0"
    pause
    exit /b 1
)

cd /d "%~dp0"
echo migrate...
"%~dp0venv\Scripts\python.exe" "%~dp0manage.py" migrate
if errorlevel 1 (
    echo ERROR: migrate failed.
    pause
    exit /b 1
)

echo seed_demo...
"%~dp0venv\Scripts\python.exe" "%~dp0seed_demo.py"

echo.
echo ========================================
echo   OK. Run START_USB.BAT
echo   Browser: http://localhost:5173
echo ========================================
echo.
pause
endlocal
exit /b 0
