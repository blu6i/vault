# 🛡️ Vault

Сервис аутентификации, авторизации и управления пользователями на базе **Python 3.14**, **FastAPI**, **GraphQL (Ariadne)** и **OAuth2/OIDC**.

Проект реализует надёжную защиту учётных данных с хэшированием **Argon2id + Pepper**, проверку сложности паролей библиотекой `zxcvbn`, генерацию и валидацию **JWT-токенов**, аудит критических событий безопасности (`audit_events`), управление OAuth-клиентами через **GraphQL API** с директивами доступа (`@isAuthenticated`, `@isAdmin`) и панель администратора.

---

## 🚀 Быстрый старт (Make)

Запуск проекта одной командой:

```bash
make init && make up && make sync && make migrate
```

### Пошаговая инструкция

1. **Инициализация окружения:**
   ```bash
   make init
   ```
   Команда создаёт файл `.env` из шаблона `.env.example` и автоматически прописывает `UID` и `GID` вашего пользователя.

2. **Настройка секретов в `.env`:**
   Откройте созданный файл `.env` и заполните обязательные параметры безопасности:
   * `JWT__SECRET_KEY` — секретный ключ подписи JWT (не менее 32 байт, можно сгенерировать через `make gen_secret`);
   * `PASSWORD__PEPPER` — статическая криптографическая соль (pepper) для хэширования паролей Argon2id;
   * `DB__POSTGRES_PASSWORD` — пароль к базе данных PostgreSQL;
   * `REDIS__PASSWORD` — пароль к Redis.

   > ⚠️ **Безопасность:** Файлы конфигурации `.env` и локальные базы данных `*.db` / `*.sqlite` внесены в `.gitignore` и **никогда не попадают в Git-репозиторий**.

3. **Запуск сервисов:**
   ```bash
   make up
   ```
   Собирает и запускает контейнеры приложения, Nginx, PostgreSQL 18 и Redis 7 в фоновом режиме.

4. **Синхронизация зависимостей:**
   ```bash
   make sync
   ```
   Устанавливает и синхронизирует зависимости проекта внутри контейнера с помощью пакетного менеджера **uv** (`uv sync`).

5. **Применение миграций:**
   ```bash
   make migrate
   ```
   Применяет актуальную схему базы данных PostgreSQL через Alembic (`alembic upgrade head`).

---

## 🌐 Доступные адреса

* **Веб-панель управления (Admin Dashboard):** [http://127.0.0.1:8080/admin/](http://127.0.0.1:8080/admin/)
* **GraphQL Playground:** [http://127.0.0.1:8080/graphql/](http://127.0.0.1:8080/graphql/)
* **Интерактивная документация REST (Swagger):** [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)
* **Проверка состояния (Healthcheck):** [http://127.0.0.1:8080/health](http://127.0.0.1:8080/health)
* **PostgreSQL:** `127.0.0.1:5432`
* **Redis:** `127.0.0.1:6379`

---

## 🛠 Стек технологий и библиотеки

* **Рантайм и управление зависимостями:** Python 3.14+, **uv** (быстрый менеджер пакетов).
* **Веб-сервер и API:**
  * **FastAPI** + **Starlette** + **Uvicorn** (ASGI);
  * **Nginx** (обратный прокси-сервер).
* **GraphQL:** **Ariadne** (Schema-First подход), GraphQL-Core (директивы схем, скаляры `DateTime`, `JSON`).
* **База данных и кэш:**
  * **PostgreSQL 18** + **SQLAlchemy 2.0** (асинхронный диалект `asyncpg`);
  * **Alembic** (миграции схемы данных);
  * **Redis 7** (`redis-py` async) для кэширования и хранения сессий.
* **Безопасность и криптография:**
  * `argon2-cffi` — современный алгоритм хэширования паролей Argon2id;
  * `zxcvbn` — проверка энтропии паролей и защита от словарных атак;
  * `python-jose`, `cryptography` — выпуск, подпись и валидация JWT-токенов.
* **Фронтенд админки:** Vanilla JavaScript, CSS Grid, HTML5 (без тяжёлых фреймворков, «голые» запросы к GraphQL и REST).
* **Качество кода и тесты:** **Pytest**, `pytest-asyncio`, `httpx`, **Ruff** (линтер и форматтер).

---

## 📋 Основные команды (Makefile)

Все операции автоматизированы через основной файл `Makefile`:

### Управление контейнерами
* `make init` — создать файл `.env` из `.env.example` с подстановкой UID/GID текущего пользователя;
* `make build` — собрать Docker-образы сервисов;
* `make up` — запустить все контейнеры в фоне;
* `make down` — остановить и удалить контейнеры;
* `make restart` — перезапустить контейнеры (`down` + `up`);
* `make ps` — посмотреть статус запущенных контейнеров;
* `make logs` — вывод логов всех сервисов (или `make logs service=app`);
* `make clean` — остановить контейнеры и удалить постоянные тома (volumes) базы данных;
* `make sh` — открыть терминал Bash внутри контейнера приложения;
* `make psql` — интерактивная консоль `psql` к PostgreSQL.

### Зависимости и стиль кода (uv & ruff)
* `make sync` — синхронизировать библиотеки через `uv sync`;
* `make lock` — зафиксировать версии зависимостей через `uv lock`;
* `make lint` — проверить код статическим анализатором `ruff check src/`;
* `make format` — автоматически отформатировать код и исправить замечания (`ruff format` + `ruff check --fix`);
* `make gen_secret` — сгенерировать надёжный криптографический ключ для `.env`.

### Миграции базы данных (Alembic)
* `make migrate` — применить миграции (`alembic upgrade head`);
* `make migration msg="название"` — сгенерировать новую миграцию на основе изменений в моделях;
* `make migrate-down` — откатить последнюю применённую миграцию (`alembic downgrade -1`).

### Тестирование (Pytest)
* `make test-db-init` — создать тестовую базу данных `app_test` и применить к ней миграции;
* `make test` — запустить набор автоматических тестов через `pytest`.

---

## 📁 Структура проекта

```text
vault/
├── docker/                 # Конфигурации Dockerfile (app, nginx, postgres)
│   ├── nginx/              # Конфигурация обратного прокси Nginx
│   ├── postgres/           # Настройки postgresql.conf
│   └── python/             # Dockerfile приложения на базе Python 3.14 + uv
├── migrations/             # Скрипты миграций схемы базы данных Alembic
│   ├── versions/           # Версии миграций
│   └── env.py              # Конфигурация окружения миграций
├── src/                    # Основной исходный код приложения
│   ├── api/                # REST API эндпоинты (v1/auth: регистрация, вход, /auth/me)
│   ├── core/               # Ядро системы:
│   │   ├── config.py       # Pydantic Settings конфигурация (загрузка .env)
│   │   ├── exceptions.py   # Базовые доменные исключения
│   │   ├── logging.py      # Настройка структурированного логирования Loguru
│   │   ├── postgres_client.py # Асинхронный клиент SQLAlchemy и сессии
│   │   ├── redis_client.py # Асинхронный пул соединений Redis
│   │   └── security.py     # Хэширование Argon2id, валидация zxcvbn, JWT
│   ├── graphql/            # GraphQL слой:
│   │   ├── schema.graphql  # SDL-схема типов, директив, запросов и мутаций
│   │   ├── schema.py       # Сборка исполняемой схемы и ASGI-приложение Ariadne
│   │   ├── context.py      # Извлечение сессии БД и текущего пользователя в контекст
│   │   ├── directives.py   # Директивы разграничения прав @isAuthenticated и @isAdmin
│   │   └── resolvers.py    # Резолверы запросов (Query) и изменений (Mutation)
│   ├── models/             # Декларативные ORM-модели SQLAlchemy:
│   │   ├── user.py         # Модель пользователей (User)
│   │   ├── oauth_client.py # Модель зарегистрированных OAuth-клиентов (OAuthClient)
│   │   ├── audit_event.py  # Модель журнала аудита безопасности (AuditEvent)
│   │   └── base.py         # Базовый декларативный класс SQLAlchemy
│   ├── repositories/       # Слой абстракции доступа к данным (User, Client, Audit)
│   ├── schemas/            # Pydantic DTO схемы запросов и ответов
│   ├── services/           # Доменная бизнес-логика (аудит, пользователи)
│   ├── static/             # Статические файлы панели администрирования:
│   │   ├── index.html      # Разметка дашборда на CSS Grid с модальными окнами
│   │   └── app.js          # Клиентский код (авторизация, вызовы GraphQL)
│   └── main.py             # Точка сборки FastAPI: CORS, роутеры, монтирование /graphql и /admin
├── tests/                  # Набор автоматических тестов (pytest)
│   ├── conftest.py         # Фикстуры тестовой БД, сессий и клиентов httpx.AsyncClient
│   ├── test_auth_flow.py   # Тестирование регистрации, входа, токенов и событий аудита
│   ├── test_graphql.py     # Тестирование GraphQL-запросов и директив доступа
│   └── test_passwords.py   # Тестирование валидации сложности паролей и хэширования
├── alembic.ini             # Конфигурационный файл Alembic
├── compose.yaml            # Манифест Docker Compose для запуска всех сервисов
├── Makefile                # Основные команды автоматизации жизненного цикла проекта
├── pyproject.toml          # Манифест зависимостей и настройки инструментов (uv, ruff, pytest)
├── uv.lock                 # Зафиксированные версии всех зависимостей
└── ROADMAP.md              # Дорожная карта реализации лабораторных работ
```

---

## 🔍 Пример работы с GraphQL

Все запросы отправляются методом **POST** на единый эндпоинт `http://127.0.0.1:8080/graphql/`.

Для обращения к защищённым полям передайте HTTP-заголовок:
```http
Authorization: Bearer <ваш_jwt_access_token>
```

### 1. Получение профиля текущего пользователя (`me`)

**POST** `http://127.0.0.1:8080/graphql/`

**Тело запроса (JSON):**
```json
{
  "query": "query { me { email } }"
}
```

**Ожидаемый ответ:**
```json
{
  "data": {
    "me": {
      "email": "admin@example.com"
    }
  }
}
```

---

### 2. Запрос списка OAuth-клиентов (требует прав администратора)

**Тело запроса (JSON):**
```json
{
  "query": "query { clients { id clientId name isConfidential redirectUris } }"
}
```

**Ожидаемый ответ:**
```json
{
  "data": {
    "clients": [
      {
        "id": "1",
        "clientId": "3f643bf4-32ac-406e-b6df-091ee389eb5d",
        "name": "Single Page Application",
        "isConfidential": false,
        "redirectUris": [
          "http://localhost:3000/callback"
        ]
      }
    ]
  }
}
```

---

### 3. Создание нового OAuth-клиента через мутацию (`createClient`)

**Тело запроса (JSON):**
```json
{
  "query": "mutation CreateClient($name: String!, $isConfidential: Boolean!, $redirectUris: [String!]) { createClient(name: $name, isConfidential: $isConfidential, redirectUris: $redirectUris) { id clientId name isConfidential redirectUris } }",
  "variables": {
    "name": "Mobile Client",
    "isConfidential": false,
    "redirectUris": ["https://myapp.example.com/oauth/callback"]
  }
}
```

**Ожидаемый ответ:**
```json
{
  "data": {
    "createClient": {
      "id": "2",
      "clientId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Mobile Client",
      "isConfidential": false,
      "redirectUris": [
        "https://myapp.example.com/oauth/callback"
      ]
    }
  }
}
```
