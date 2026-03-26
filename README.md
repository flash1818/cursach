# Real Estate Pro (Django + React/Vite)

Проект состоит из двух частей:
- **Backend**: Django + Django REST Framework (API и HTML-страницы входа/профиля)
- **Frontend**: React-приложение на **Vite** (витрина объектов, аналитика, избранное)

По умолчанию запускаются одновременно:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

---

## Быстрый старт (Windows, рекомендовано)

### 1) Предварительные требования
- **Python**: 3.10+ (проект на Django `6.0.3`)
- **Node.js + npm**: для фронтенда (Vite/React)
- **Опционально (только если хотите PostgreSQL)**: PostgreSQL 14+ (можно поставить вместе с pgAdmin)

Что именно скачать:
- Python: установщик с python.org (важно включить “Add Python to PATH”)
- Node.js: LTS-версия с nodejs.org (npm идёт в комплекте)
- PostgreSQL (опционально): installer с postgresql.org

### 2) Backend (Django)
1. Перейдите в корень проекта (`cursmav`) и создайте/активируйте виртуальное окружение:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Установите зависимости backend:
   ```powershell
   pip install -r requirements.txt
   ```
3. Примените миграции:
   ```powershell
   python manage.py migrate
   ```
4. (Опционально, но удобно) Загрузите демо-данные (после `migrate`):
   ```powershell
   python seed_demo.py
   ```
   После этого появится риэлтор-демо:
   - логин: `demo_realtor`
   - пароль: `demo_realtor_pass`

### 3) Frontend (React/Vite)
1. Перейдите в папку frontend:
   ```powershell
   cd frontend
   ```
2. Установите зависимости:
   ```powershell
   npm install
   ```

### 4) Запуск
#### Вариант A (самый простой): SQLite + запуск по отдельности
- Backend:
  ```powershell
  .\venv\Scripts\activate
  python manage.py migrate
  python manage.py runserver 0.0.0.0:8000
  ```
- Frontend (в новом окне терминала):
  ```powershell
  cd frontend
  npm run dev -- --host 0.0.0.0 --port 5173
  ```

#### Вариант B (одним файлом): `run_project.bat`
Запуск:
```powershell
.\run_project.bat
```

Он поднимает и Django, и Vite.

Важно: сейчас в `run_project.bat` **включен PostgreSQL** (`USE_POSTGRES=1`) и прописан пароль. Если PostgreSQL не установлен/не настроен — откройте `run_project.bat` и поставьте `set USE_POSTGRES=0` (или удалите строку), тогда будет SQLite.

#### Важно для фронтенда (API / ссылки на backend)
По умолчанию фронтенд ходит в API по пути `/api` (через proxy Vite) и открывает страницы входа/профиля на `http://localhost:8000`.
Если запускаете backend на другом адресе/порту (или открываете фронтенд по IP), используйте переменные Vite:
1) Скопируйте пример:
```powershell
Copy-Item .\frontend\.env.example .\frontend\.env.local
```
2) Отредактируйте `frontend\.env.local` при необходимости:
- `VITE_API_BASE` (например `http://<IP>:8000/api`)
- `VITE_BACKEND_ORIGIN` (например `http://<IP>:8000`)

#### Если вы видите CORS-ошибки
В `realestate_site/settings.py` разрешён origin `http://localhost:5173`. Если фронтенд открывается не с `localhost`, добавьте нужный origin в `CORS_ALLOWED_ORIGINS`.

### 5) Что открыть в браузере
- Интерфейс React: `http://localhost:5173`
- HTML-вход/регистрация (используются для сессии): `http://localhost:8000/auth/login/`, `http://localhost:8000/auth/register/`
- Профиль: `http://localhost:8000/profile/`

---

## База данных: SQLite или PostgreSQL

### SQLite (по умолчанию)
Django будет использовать файл базы `db.sqlite3` в корне проекта.

### PostgreSQL
Подключение включается переменной окружения `USE_POSTGRES=1`.

В `realestate_site/settings.py` используются переменные:
- `POSTGRES_DB` (по умолчанию `realestate_db`)
- `POSTGRES_USER` (по умолчанию `postgres`)
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST` (по умолчанию `localhost`)
- `POSTGRES_PORT` (по умолчанию `5432`)

Перед запуском:
1. Убедитесь, что PostgreSQL запущен
2. Создайте БД/пользователя (если они отсутствуют)
3. Запустите `python manage.py migrate`
4. По желанию `python seed_demo.py`

---

## Демонстрационный режим фронтенда

Если в базе **нет** объектов (например, вы не прогнали `seed_demo.py` или миграции), то фронтенд всё равно покажет демо-объекты из `frontend/src/data/demoData.js`.

Но:
- избранное и другие “живые” данные будут зависеть от API и авторизации
- для риэлтора удобнее всё же сделать `python seed_demo.py`

---

## REST API (base: `/api/`)

Все API находятся под:
- `http://localhost:8000/api/`

Основные эндпоинты:
- `GET/POST /api/property-types/`
- `GET/POST /api/cities/`
- `GET/POST /api/districts/` (можно фильтровать параметром `?city=<id>`)
- `GET/POST /api/properties/`
- `GET/POST /api/property-images/`
- `GET/POST /api/inquiries/`
- `GET/POST /api/favorites/`
- `GET/POST /api/my/properties/` (для риэлтора, требуется авторизация)

А также:
- `GET /api/analytics/`
- `POST /api/auth/login/`
- `POST /api/auth/register/` (регистрация доступна только клиентам)
- `POST /api/auth/logout/`
- `GET /api/auth/me/`

---

## Авторизация и cookies (важно)

React делает запросы на backend с `credentials: 'include'`, то есть использует **session cookies** Django.

Также в backend есть специальная аутентификация:
- `CsrfExemptSessionAuthentication` — для API-запросов от SPA отключает проверку CSRF

Это **не рекомендуется** для публичного деплоя без дополнительной защиты.

Если вы открываете фронтенд **не с `localhost`** (например, с другого ПК по IP), то могут всплыть CORS-ошибки: в `realestate_site/settings.py` разрешён только `http://localhost:5173`. Тогда добавьте ваш origin в `CORS_ALLOWED_ORIGINS`.

---

## Траблшутинг

1. **Не запускается PostgreSQL**
   - проверьте `POSTGRES_HOST/POSTGRES_PORT`
   - убедитесь, что указанный пользователь имеет права на БД
2. **При ошибках после установки**
   - сначала: `python manage.py migrate`
   - затем: `python seed_demo.py` (если хотите демо-данные)
3. **Порт занят**
   - backend: `8000`
   - frontend: `5173`
   - поменяйте порты и в `run_project.bat`/командах запуска тоже.

---

## Публикация на GitHub

Важно: перед публикацией проверьте, что вы не коммитите секреты.
В проекте **не должно** быть:
- паролей к БД
- `DJANGO_SECRET_KEY` для production
- `.env.local` / `.env` с токенами

Пароль PostgreSQL для запуска нужно задавать через переменные окружения (а не хранить в репозитории), например:
```powershell
set POSTGRES_PASSWORD=123123
.\run_project.bat
```

Для Django `SECRET_KEY` тоже берётся из переменной:
```powershell
set DJANGO_SECRET_KEY=dev-secret
```

### 1) Подготовьте `.gitignore`
Поскольку в корне нет `.gitignore`, добавьте хотя бы:
- `venv/`, `venvvenv/`, `venv_broken_py313/`
- `frontend/node_modules/`
- `db.sqlite3`
- `.env*`

### 2) Залейте проект
1. Создайте пустой репозиторий на GitHub (например, `realestate-pro`)
2. На ПК в корне проекта выполните:
```powershell
git init
git add -A
git commit -m "Initial commit: Django + React/Vite"
git branch -M main
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

После этого репозиторий будет доступен на GitHub.

---

## “Открывается с БД” после клонирования

Сам GitHub сам по себе не запускает БД автоматически, поэтому “чтобы оно работало” обычно означает: после `git clone` вы можете поднять backend и БД локально в вашей среде.

### Вариант A: SQLite (без отдельного сервера БД)
1. `python manage.py migrate`
2. `python seed_demo.py` (опционально)
3. `python manage.py runserver 0.0.0.0:8000`

SQLite используется по умолчанию, когда `USE_POSTGRES` не включён.

### Вариант B: PostgreSQL (требуются переменные окружения)
1. Поднимите PostgreSQL (локально или через ваш инструмент: Docker, hosting, и т.п.)
2. Выставьте переменные (пример):
   - `USE_POSTGRES=1`
   - `POSTGRES_DB=...`
   - `POSTGRES_USER=...`
   - `POSTGRES_PASSWORD=...`
   - `POSTGRES_HOST=...` (например, `localhost` или имя сервиса в Docker)
   - `POSTGRES_PORT=5432`
3. Затем:
   - `python manage.py migrate`
   - `python seed_demo.py` (опционально)

---

## Если вы хотите “запуск внутри GitHub”

Если под “там же” вы имели в виду GitHub Codespaces (запуск прямо в облаке GitHub):
- потребуется добавить `.devcontainer/` (devcontainer + docker-compose для PostgreSQL)
- и (важно) учесть, что `run_project.bat` — Windows-скрипт; в Codespaces нужен Linux-скрипт (`.sh`) или кроссплатформенный запуск.

Скажите, какой вариант вам нужен:
1) `SQLite после clone` (самый простой)
2) `Postgres локально через Docker Compose`
3) `Codespaces + PostgreSQL внутри GitHub`

И я под это обновлю README точнее (и при желании могу добавить devcontainer/docker-compose файлы в проект).

