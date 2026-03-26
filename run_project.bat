@echo off
setlocal EnableExtensions

REM Запуск Django-сервера и фронтенда Vite одним батником
REM Backend:  http://0.0.0.0:8000  (доступен по IP в локальной сети)
REM Frontend: http://0.0.0.0:5173  (доступен по IP в локальной сети)

cd /d "%~dp0"

echo [1/2] Запуск backend (Django)...

REM ---- PostgreSQL (если нужно) ----
REM Если PostgreSQL не нужен/не настроен — поставьте USE_POSTGRES=0 (SQLite).
set USE_POSTGRES=1
set POSTGRES_DB=realestate_db
set POSTGRES_USER=realestate_user
REM ВАЖНО: не храните пароль в репозитории.
REM Установите пароль через переменную окружения перед запуском, например:
REM   set POSTGRES_PASSWORD=123123
REM   run_project.bat
if "%POSTGRES_PASSWORD%"=="" (
  set POSTGRES_PASSWORD=
)
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432

REM Доп. защита от проблем с кодировкой сообщений PostgreSQL на Windows
set PGCLIENTENCODING=UTF8

REM ---- Выбор Python для backend ----
set "VENV_PY=%cd%\venv\Scripts\python.exe"
set "FALLBACK_SITEPACKAGES=%cd%\venv_broken_py313\Lib\site-packages"
set "FALLBACK_PY=py -3.14"

if exist "%VENV_PY%" goto check_venv
goto run_fallback

:check_venv
"%VENV_PY%" -c "import django" >nul 2>nul
if errorlevel 1 goto run_fallback
goto run_venv

:run_venv
echo Использую venv (Django установлен).
start "Django server" cmd /c "\"%VENV_PY%\" -u manage.py runserver 0.0.0.0:8000 --noreload"
goto run_frontend

:run_fallback
echo venv без Django (или venv отсутствует): запускаю backend через fallback PYTHONPATH.
echo Рекомендуется починить окружение: pip install -r requirements.txt
start "Django server" cmd /c "set \"PYTHONPATH=%FALLBACK_SITEPACKAGES%\" && set \"USE_POSTGRES=0\" && %FALLBACK_PY% -u manage.py runserver 0.0.0.0:8000 --noreload"

:run_frontend
echo [2/2] Запуск frontend (Vite)...
cd "frontend"
start "Vite dev server" cmd /c "npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo Серверы запущены.
echo Backend:  http://localhost:8000/ (локально)  /  http://^<IP_ЭТОГО_ПК^>:8000/ (в сети)
echo Frontend: http://localhost:5173/ (локально)  /  http://^<IP_ЭТОГО_ПК^>:5173/ (в сети)
echo.
echo Окно можно закрыть, процессы продолжают работать в отдельных консолях.

endlocal
pause
