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
| **`install.bat`** | Удаляет старый `venv`, создаёт новый на **этом** ПК (иначе бывает ошибка «No Python at …Python312»), ставит `pip`/`npm`, `migrate`, `seed_demo` |
| **`run_project.bat`** | Два окна: Django :8000 и Vite :5173 (SQLite) |

Порядок:
1. Скопируйте папку проекта на флешку / на диск.
2. На **каждом новом компьютере** один раз **`install.bat`** (нужен интернет).
3. Работа с проектом — **`run_project.bat`**.

Сообщения в батниках на **английском** специально: так `cmd.exe` на русской Windows не ломает разбор файла из‑за UTF‑8/кириллицы.

### Если что-то пошло не так

- «Python не найден» / «Node не найден» — установите и перезапустите терминал.
- Ошибка `pip` / `npm` — проверьте интернет или снова **`install.bat`**.
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
python seed_demo_no_images.py
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
- Во **frontend** (файл `frontend/.env.local` или переменные сборки): `VITE_YANDEX_MAPS_API_KEY` — ключ [JavaScript API и Геосаджеста](https://developer.tech.yandex.ru/) для карты на витрине; без ключа Яндекс.Карты могут не отображаться.

---

## База данных

- **По умолчанию** (в т.ч. `run_project.bat`): **SQLite**, файл `db.sqlite3` в корне.
- **PostgreSQL:** задайте `USE_POSTGRES=1` и переменные `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, затем `migrate`.

---

## Демо-данные и API

После `seed_demo_no_images.py` создаются учётные записи ниже (пароли при каждом запуске сидера сбрасываются на указанные).

### Админка Django

- **URL:** [http://localhost:8000/internal-admin-only/](http://localhost:8000/internal-admin-only/)  
  (путь намеренно нестандартный — см. `realestate_site/urls.py`.)
- **Логин:** `demo_admin`
- **Пароль:** `demo_admin_pass`

### Демо-риэлтор (вход на сайт / кабинет)

- **Логин:** `demo_realtor`
- **Пароль:** `demo_realtor_pass`  
- Страница входа: [http://localhost:8000/auth/login/](http://localhost:8000/auth/login/)

REST API: `http://localhost:8000/api/` (список эндпоинтов см. в коде `listings/urls.py`).

Фронт ходит в API через Vite proxy (`/api`). HTML-страницы входа/профиля проксируются с тем же origin при работе через `localhost:5173`.

### Витрина React и кнопка «К сделке»

Сессия привязана к **origin** (хост + порт). Если войти только на `http://localhost:8000`, а каталог открыт на `http://localhost:5173`, cookie не попадёт в запросы к API с витрины — уведомления и избранное не заработают.

**Вход для работы с витриной:** откройте **`http://localhost:5173/auth/login/`** (или ссылку «Войти» в шапке SPA — она ведёт на тот же порт, что и каталог).

Каждый запуск **`seed_demo_no_images.py`** очищает **уведомления и сделки**, возвращает объекты со статусов «Продан»/«Архив» в **«Активный»**. Демо-фото в Django **`media/`** по умолчанию не создаются (включить можно так: `LOAD_DEMO_IMAGES=1 python seed_demo_no_images.py`). Если файлов нет — заглушки показываются на фронтенде.

---

## Авторизация

Используются **session cookies** Django. Для API в dev отключена проверка CSRF на части эндпоинтов — для публичного интернета нужна дополнительная защита.
