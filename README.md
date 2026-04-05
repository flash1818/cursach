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
python -m daphne -b 0.0.0.0 -p 8000 realestate_site.asgi:application
```

### Frontend (второе окно)
```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### Переменные окружения
- В корне проекта создайте файл **`.env`** (в репозиторий он не попадает). Образец полей — **`.env.example`**.
- **`DJANGO_SECRET_KEY`** — обязательно задайте свой в продакшене; не храните реальные ключи в коде и в коммитах.
- `USE_POSTGRES=1` и `POSTGRES_*` — если используете PostgreSQL вместо SQLite.
- Во **frontend** (`frontend/.env.local` или переменные сборки): **`VITE_YANDEX_MAPS_API_KEY`** — ключ [JavaScript API и Геосаджеста](https://developer.tech.yandex.ru/) для карты; без ключа карта может не отображаться.

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
- **Пароль:** `                                                   `  
- Страница входа: [http://localhost:8000/auth/login/](http://localhost:8000/auth/login/)

REST API: `http://localhost:8000/api/` (маршруты в `listings/urls.py`). Примеры:
- `GET /api/similar/<id>/` — до 3 похожих объектов (город, комнаты, коридор цены, этаж, метро).
- `GET /api/my/stats/dashboard/` — статистика риэлтора (просмотры, заявки «К сделке», конверсия, срок до закрытия сделки).
- `POST /api/upload-photo/` — массовая загрузка фото (`multipart`, поля `property`, `images`).
- `GET /api/auth/csrf/` — выставляет cookie `csrftoken` для POST из SPA.

**WebSocket (чат «Спросить о цене» на витрине):** `ws://localhost:5173/ws/chat/<id>/` через прокси Vite на Daphne. Для WS backend должен работать через **Daphne** (см. `run_project.bat`), а не только `runserver`.

Фронт ходит в API через Vite proxy (`/api`). HTML-страницы входа/профиля проксируются с тем же origin при работе через `localhost:5173`.

### Витрина React и кнопка «К сделке»

Сессия привязана к **origin** (хост + порт). Если войти только на `http://localhost:8000`, а каталог открыт на `http://localhost:5173`, cookie не попадёт в запросы к API с витрины — уведомления и избранное не заработают.

**Вход для работы с витриной:** откройте **`http://localhost:5173/auth/login/`** (или ссылку «Войти» в шапке SPA — она ведёт на тот же порт, что и каталог).

Каждый запуск **`seed_demo_no_images.py`** очищает **уведомления и сделки** и возвращает объекты со статусов «Продан»/«Архив» в **«Активный»**. Загруженные фотографии в Django **`media/`** сидер не перезаписывает и не удаляет.

---

## Авторизация и CSRF

Используются **session cookies** Django. Для запросов из React (и fetch в кабинете риэлтора) включена стандартная проверка **CSRF**: при загрузке витрины вызывается `GET /api/auth/csrf/` (`ensure_csrf_cookie`), в браузере появляется cookie `csrftoken`, а POST/DELETE уходят с заголовком **`X-CSRFToken`** и **`credentials: 'include'`** (тот же origin, что и у Vite-прокси).

---

## Позиционирование продукта (кратко для инвестора / заказчика)

Платформа сочетает надёжный бэкенд на Django, современную витрину на React и сценарий полной автономности (в т.ч. запуск с флешки). Поведенческий подбор похожих объектов, чат в реальном времени по объекту, дашборд риэлтора с графиками и массовая загрузка фото на базе уже настроенного `media/` дают заметное UX-преимущество без смены основной архитектуры — конкурентам с «голым» каталогом для догона часто пришлось бы переписывать серверную часть и инфраструктуру (в т.ч. ASGI для WebSocket).
