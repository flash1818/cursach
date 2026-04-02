@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM =============================================================================
REM  Установка зависимостей проекта (один раз на новом ПК или после копии с флешки)
REM  Требуется: Python 3.10+ и Node.js (npm) в PATH. Первый запуск — доступ в интернет
REM  (pip и npm качают пакеты). Работает из любой папки / с любой буквы диска.
REM =============================================================================

cd /d "%~dp0"
echo.
echo === Real Estate Pro — установка зависимостей ===
echo Папка проекта: %cd%
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ОШИБКА] Python не найден. Установите с https://www.python.org/ 
  echo         Отметьте "Add Python to PATH".
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo [ОШИБКА] Node.js не найден. Установите LTS с https://nodejs.org/
  pause
  exit /b 1
)

echo [1/5] Python:
python --version
echo [2/5] Node:
node -v
npm -v
echo.

if not exist "venv\Scripts\python.exe" (
  echo [3/5] Создаю виртуальное окружение venv...
  python -m venv venv
  if errorlevel 1 (
    echo [ОШИБКА] Не удалось создать venv. Попробуйте: py -3.12 -m venv venv
    pause
    exit /b 1
  )
) else (
  echo [3/5] Папка venv уже есть — пропускаю создание.
)

echo [4/5] Устанавливаю Python-зависимости (pip)...
call "%cd%\venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install --default-timeout=120 -r requirements.txt
if errorlevel 1 (
  echo [ОШИБКА] pip install не удался. Проверьте интернет или прокси.
  pause
  exit /b 1
)

echo [5/5] Устанавливаю frontend (npm install)...
cd /d "%cd%\frontend"
call npm install
if errorlevel 1 (
  echo [ОШИБКА] npm install не удался.
  cd /d "%~dp0"
  pause
  exit /b 1
)
cd /d "%~dp0"

echo.
echo Применяю миграции базы (SQLite)...
call "%cd%\venv\Scripts\activate.bat"
python manage.py migrate
if errorlevel 1 (
  echo [ОШИБКА] migrate не удался.
  pause
  exit /b 1
)

echo.
echo Загружаю демо-данные (seed_demo.py)...
python seed_demo.py
if errorlevel 1 (
  echo [ПРЕДУПРЕЖДЕНИЕ] seed_demo завершился с ошибкой — можно запустить вручную позже.
)

echo.
echo =============================================================================
echo  Готово. Дальше запускайте: start_usb.bat
echo  Сайт: http://localhost:5173   API: http://localhost:8000
echo =============================================================================
echo.
pause
endlocal
exit /b 0
