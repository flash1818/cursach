# Real Estate Pro (Django + React/Vite)

Проект: **backend** (Django + DRF) и **frontend** (React + Vite).

После запуска:
- **Сайт:** `http://localhost:5173`
- **API / HTML-вход:** `http://localhost:8000`

---

## Запуск с флешки (Windows) — два батника

На новом ПК один раз нужны **Python 3.10+** и **Node.js (LTS)** с [python.org](https://www.python.org/) и [nodejs.org](https://nodejs.org/) (галочка «Add Python to PATH»).  
Первый запуск установки — **интернет** (pip и npm скачивают пакеты).

| Файл | Назначение |
|------|------------|
| **`install_usb.bat`** | Создаёт `venv`, ставит зависимости (`pip`, `npm`), `migrate`, `seed_demo` |
| **`run_project.bat`** | Запускает Django и Vite (база **SQLite**, два окна) |

Порядок:
1. Скопируйте папку проекта на флешку / на диск.
2. Дважды щёлкните **`install_usb.bat`** (дождитесь «Готово»).
3. Когда нужно работать с проектом — **`run_project.bat`**.

Сообщения в батниках на **английском** специально: так `cmd.exe` на русской Windows не ломает разбор файла из‑за UTF‑8/кириллицы.

### Если что-то пошло не так

- «Python не найден» / «Node не найден» — установите и перезапустите терминал.
- Ошибка `pip` / `npm` — проверьте интернет или запустите `install_usb.bat` ещё раз.
- Порты **8000** и **5173** должны быть свободны.

---

## Ручная установка (без батников)

### Требования
- Python 3.10+
- Node.js + npm
- Опционально: PostgreSQL (если нужна не SQLite)

### Backend
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python seed_demo.py
python manage.py runserver 0.0.0.0:8000
```

### Frontend (второе окно)
```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### Переменные окружения (по желанию)
- `DJANGO_SECRET_KEY` — секрет Django (для продакшена задайте свой).
- `USE_POSTGRES=1` и `POSTGRES_*` — если используете PostgreSQL вместо SQLite.

---

## База данных

- **По умолчанию** (в т.ч. `run_project.bat`): **SQLite**, файл `db.sqlite3` в корне.
- **PostgreSQL:** задайте `USE_POSTGRES=1` и переменные `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, затем `migrate`.

---

## Демо-данные и API

После `seed_demo.py` есть демо-риэлтор: логин **`demo_realtor`**, пароль **`demo_realtor_pass`**.

REST API: `http://localhost:8000/api/` (список эндпоинтов см. в коде `listings/urls.py`).

Фронт ходит в API через Vite proxy (`/api`). HTML-страницы входа/профиля проксируются с тем же origin при работе через `localhost:5173`.

---

## Авторизация

Используются **session cookies** Django. Для API в dev отключена проверка CSRF на части эндпоинтов — для публичного интернета нужна дополнительная защита.
