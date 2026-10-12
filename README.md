# 🛡️ Vault

Сервис аутентификации, авторизации и управления пользователями на базе **Python 3.14**, **FastAPI**, **GraphQL** и **OAuth2/OIDC**.

---

## 🛠 Стек технологий

* **Backend:** Python 3.14, FastAPI, Uvicorn, uv
* **API:** GraphQL (Ariadne) & REST
* **База данных:** PostgreSQL 18 (SQLAlchemy 2.0, asyncpg, Alembic)
* **Кэш и сессии:** Redis 7
* **Веб-интерфейс:** SSR (Jinja2)
* **Линтинг и тесты:** Ruff, Pytest

---

## 🚀 Быстрый старт

Запуск проекта одной командой:

```bash
make init && make up && make sync && make migrate
```

1. `make init` — создаёт `.env` файл из `.env.example`.
2. `make up` — собирает и запускает контейнеры в фоне.
3. `make sync` — синхронизирует Python-зависимости.
4. `make migrate` — применяет миграции базы данных.

### Доступные адреса
* **Healthcheck:** [http://127.0.0.1:8080/health](http://127.0.0.1:8080/health)
* **API Docs (Swagger):** [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)
* **GraphQL Playground:** [http://127.0.0.1:8080/graphql](http://127.0.0.1:8080/graphql)
* **PostgreSQL:** `127.0.0.1:5432`
* **Redis:** `127.0.0.1:6379`

---

## 📋 Основные команды (Makefile)

### Контейнеры
* `make up` / `make down` — запуск / остановка контейнеров.
* `make restart` — быстрый перезапуск.
* `make logs` — просмотр логов (`make logs service=app`).
* `make sh` — вход в терминал контейнера приложения.
* `make psql` — консоль PostgreSQL.
* `make clean` — остановка и удаление контейнеров вместе с томами БД.

### Разработка и зависимости
* `make sync` — установка/синхронизация библиотек (`uv sync`).
* `make lock` — обновление `uv.lock`.
* `make lint` — проверка линтером Ruff.
* `make format` — автоформатирование кода.

### Миграции (Alembic)
* `make migrate` — применить миграции к БД.
* `make migration msg="описание"` — создать новую миграцию.
* `make migrate-down` — откатить последнюю миграцию.

### Тестирование
* `make test-db-init` — создать тестовую БД и применить миграции.
* `make test` — запустить тесты (Pytest).

---

## 📁 Структура проекта

```text
├── docker/                 # Конфигурации Dockerfile (app, nginx, postgres)
├── migrations/             # Миграции схемы БД Alembic
├── src/
│   ├── api/                # REST-эндпоинты и зависимости
│   ├── core/               # Конфигурация, клиенты БД/Redis, безопасность
│   ├── graphql/            # Схема и резолверы GraphQL
│   ├── models/             # ORM-модели базы данных
│   ├── schemas/            # Pydantic DTO схемы
│   ├── services/           # Бизнес-логика
│   ├── web/                # SSR веб-интерфейс (шаблоны Jinja2, статика)
│   └── main.py             # Точка входа FastAPI
├── tests/                  # Тесты
├── compose.yaml            # Docker Compose
├── Makefile                # Команды автоматизации
├── pyproject.toml          # Зависимости и конфигурации утилит
└── ROADMAP.md              # Дорожная карта реализации по лабораторным работам
```
