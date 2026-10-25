# FastAPI + Next.js Auth

Fullstack-приложение с регистрацией, входом по JWT в httpOnly cookie и управлением каталогом товаров.

- **Backend** — FastAPI, асинхронный SQLAlchemy 2.0, PostgreSQL, Alembic
- **Frontend** — Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, axios
- **Инфраструктура** — Docker, docker-compose

## Возможности

- Регистрация и вход по email и паролю
- Пароли хранятся в виде bcrypt-хеша
- JWT выдаётся в **httpOnly cookie** — JavaScript на странице не имеет доступа к токену
- Альтернативно токен принимается в заголовке `Authorization: Bearer <token>` (для Swagger и API-клиентов)
- Просмотр списка товаров доступен всем, создание / изменение / удаление — только авторизованным
- Включение и выключение товара (`is_active`), проверка уникальности названия и минимальной цены
- Понятные сообщения об ошибках FastAPI на фронтенде (включая ошибки валидации 422)

## Структура проекта

```
.
├── docker-compose.yaml        # postgres + backend + frontend
├── .env                       # переменные окружения backend (не коммитится)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrations/            # миграции Alembic (users, products)
│   ├── app/
│   │   ├── main.py            # создание приложения, CORS, роутеры
│   │   ├── api/
│   │   │   ├── deps.py        # get_current_user: токен из cookie или Bearer
│   │   │   └── v1/
│   │   │       ├── auth.py    # /auth/*
│   │   │       └── product.py # /products/*
│   │   ├── core/
│   │   │   ├── config.py      # настройки (pydantic-settings, .env)
│   │   │   ├── database.py    # async engine и сессия
│   │   │   └── security.py    # bcrypt, создание и проверка JWT
│   │   ├── models/            # SQLAlchemy-модели UserModel, ProductModel
│   │   ├── schemas/           # Pydantic-схемы запросов и ответов
│   │   ├── repositories/      # работа с БД
│   │   └── services/          # бизнес-логика (AuthService, ProductService)
│   └── tests/                 # pytest: схемы, репозитории, сервисы, API
└── frontend/
    ├── Dockerfile             # многоэтапная сборка, standalone-режим Next.js
    ├── .env.local             # NEXT_PUBLIC_API_URL (не коммитится)
    └── src/
        ├── app/
        │   ├── page.tsx           # вход
        │   ├── register/page.tsx  # регистрация
        │   └── products/page.tsx  # список товаров, выход
        ├── components/
        │   ├── ProductCard.tsx    # карточка: вкл/выкл, удаление
        │   └── ProductForm.tsx    # форма добавления товара
        └── lib/api.ts             # axios-клиент, типы, обработка ошибок
```

Backend построен по слоям: **роутер → сервис → репозиторий → модель**. Роутеры переводят исключения сервисов в HTTP-коды, сервисы содержат бизнес-правила, репозитории — запросы к БД.

## API

| Метод  | Путь                    | Доступ        | Описание                                           |
|--------|-------------------------|---------------|----------------------------------------------------|
| POST   | `/auth/register`        | все           | Регистрация. `201`, `409` если email занят         |
| POST   | `/auth/login`           | все           | Вход, ставит cookie с JWT. `401` при неверных данных |
| POST   | `/auth/logout`          | все           | Удаляет cookie. `204`                              |
| GET    | `/auth/me`              | авторизованные | Текущий пользователь                              |
| GET    | `/products/`            | все           | Список товаров                                     |
| POST   | `/products/`            | авторизованные | Создать товар. `409` если название занято         |
| PATCH  | `/products/{id}`        | авторизованные | Частичное обновление (`title`, `price`, `is_active`) |
| DELETE | `/products/{id}`        | авторизованные | Удалить товар. `204`, `404` если не найден        |

Интерактивная документация: http://localhost:8000/docs

### Правила валидации

- **Email** приводится к нижнему регистру — `User@Mail.com` и `user@mail.com` считаются одним аккаунтом
- **Пароль** — от 8 символов и не более 72 байт (ограничение bcrypt; кириллический символ занимает 2 байта)
- **Название товара** — от 2 до 100 символов, уникальное
- **Цена** — не меньше 1.00

## Как работает авторизация

1. Фронтенд отправляет `POST /auth/login` с email и паролем.
2. Backend проверяет пароль, создаёт JWT (`sub` = id пользователя, срок — `ACCESS_TOKEN_EXPIRE_MINUTES`) и ставит его в cookie с флагами `HttpOnly` и `SameSite=Lax`.
3. axios-клиент создан с `withCredentials: true`, поэтому браузер сам прикладывает cookie ко всем запросам к API.
4. `get_current_user` берёт токен из cookie (или из заголовка Bearer), проверяет подпись и срок действия и загружает пользователя из БД. Неактивный пользователь получает `401`.
5. `POST /auth/logout` удаляет cookie.

Cookie сессионная: браузер удаляет её при закрытии, а сам JWT истекает через заданное время.

## Переменные окружения

### `.env` в корне проекта (backend)

| Переменная                    | По умолчанию   | Описание                                         |
|-------------------------------|----------------|--------------------------------------------------|
| `DB_HOST`                     | —              | Хост PostgreSQL (в docker-compose переопределяется на `postgres`) |
| `DB_PORT`                     | —              | Порт PostgreSQL                                  |
| `DB_USER`                     | —              | Пользователь БД                                  |
| `DB_PASS`                     | —              | Пароль БД                                        |
| `DB_NAME`                     | —              | Имя БД                                           |
| `JWT_SECRET_KEY`              | обязательна    | Секрет для подписи JWT                           |
| `JWT_ALGORITHM`               | `HS256`        | Алгоритм подписи                                 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60`           | Время жизни токена                               |
| `AUTH_COOKIE_NAME`            | `access_token` | Имя cookie с токеном                             |
| `AUTH_COOKIE_SECURE`          | `false`        | `true` на проде с HTTPS                          |

Пример для docker-compose (данные совпадают с сервисом `postgres`):

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
DB_NAME=app_db
JWT_SECRET_KEY=замените-на-длинную-случайную-строку
```

Сгенерировать секрет: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

### `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Переменные `NEXT_PUBLIC_*` встраиваются в JS при сборке, поэтому в Docker адрес API передаётся как build-arg.

## Запуск через Docker

```bash
docker compose up --build
```

- Frontend — http://localhost:3000
- Backend — http://localhost:8000 (Swagger — http://localhost:8000/docs)
- PostgreSQL — `localhost:5432`

При старте backend-контейнер выполняет `alembic upgrade head`, затем запускает uvicorn.

## Локальный запуск без Docker

### Backend

Нужны Python 3.11+ и запущенный PostgreSQL (например, только сервис из compose: `docker compose up postgres`).

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

Нужен Node.js 20+.

```bash
cd frontend
npm install
npm run dev
```

CORS на backend разрешает запросы с `http://localhost:3000` и `http://127.0.0.1:3000`.

## Тесты

Тесты используют SQLite в памяти, поэтому PostgreSQL для них не нужен. Тестовые зависимости не входят в `requirements.txt` и ставятся отдельно:

```bash
cd backend
pip install pytest pytest-asyncio aiosqlite
pytest
```

Покрыты схемы, репозитории, сервисы, авторизация и HTTP-эндпоинты.
