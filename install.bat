@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%CD%"

echo.
echo ========================================
echo   INSTALL - Real Estate Pro
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not in PATH. Install from python.org
    pause
    exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not in PATH. Install from nodejs.org
    pause
    exit /b 1
)

echo Removing old venv - fixes broken Python path after copy from another PC.
if exist "%ROOT%\venv" rmdir /s /q "%ROOT%\venv"

echo Creating new venv on THIS computer...
python -m venv "%ROOT%\venv"
if errorlevel 1 (
    echo ERROR: Cannot create venv. Try: py -3.12 -m venv venv
    pause
    exit /b 1
)

echo pip install...
"%ROOT%\venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto BAD

"%ROOT%\venv\Scripts\python.exe" -m pip install --default-timeout=120 -r "%ROOT%\requirements.txt"
if errorlevel 1 goto BAD

echo npm install...
pushd "%ROOT%\frontend"
call npm install
if errorlevel 1 (
    popd
    goto BAD
)
popd

echo migrate...
"%ROOT%\venv\Scripts\python.exe" "%ROOT%\manage.py" migrate
if errorlevel 1 goto BAD

echo seed...
"%ROOT%\venv\Scripts\python.exe" "%ROOT%\seed_demo.py"

echo.
echo ========================================
echo   OK. Run RUN_PROJECT.BAT
echo   Then open browser: localhost port 5173
echo ========================================
echo.
pause
endlocal
exit /b 0

:BAD
echo.
echo INSTALL FAILED.
pause
endlocal
exit /b 1
