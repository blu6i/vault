# Production-Ready Backend Template (Python + FastAPI)

Шаблон асинхронного бэкенда на базе **Python 3.13+**, **FastAPI**, **SQLAlchemy 2.0 (asyncpg)**, **PostgreSQL 18**, **Redis 7**, **Nginx** и менеджера пакетов **uv**.

---

## Быстрый старт

```bash
make init && make up && make sync && make migrate
```

1. `make init` — создаёт `.env` с UID/GID текущего пользователя хоста.
2. `make up` — собирает и запускает контейнеры в фоне.
3. `make sync` — синхронизирует Python-зависимости через `uv sync`.
4. `make migrate` — применяет миграции Alembic к PostgreSQL.

После запуска:
- **API & Healthcheck**: http://127.0.0.1:8080/health
- **Swagger Docs**: http://127.0.0.1:8080/docs *(доступен при `DEBUG=true`)*
- **PostgreSQL**: `127.0.0.1:5432` *(логин `admin`, пароль из `.env`)*
- **Redis**: `127.0.0.1:6379` *(пароль из `.env`)*

---

## Основные команды Makefile

### Управление контейнерами
- `make up` / `make down` — запуск / остановка сервисов.
- `make restart` — быстрый перезапуск.
- `make ps` — статус запущенных контейнеров.
- `make logs` — просмотр логов всех сервисов (`make logs service=app`).
- `make sh` — вход в bash-терминал контейнера приложения.
- `make psql` — вход в интерактивную консоль PostgreSQL.
- `make clean` — полная очистка (`down -v` с удалением БД).

### Разработка и качество кода
- `make sync` — установка/обновление библиотек (`uv sync`).
- `make lock` — фиксация дерева зависимостей в `uv.lock`.
- `make lint` — проверка линтером Ruff.
- `make format` — автоформатирование и автофиксы (Ruff).

### База данных и миграции (Alembic)
- `make migrate` — применить миграции (`alembic upgrade head`).
- `make migration msg="описание"` — сгенерировать новую ревизию с автогенерацией.
- `make migrate-down` — откатить последнюю миграцию (`downgrade -1`).

### Тестирование (Pytest)
- `make test-db-init` — создать тестовую БД `app_test` и применить к ней миграции.
- `make test` — запустить тесты (требует предварительного вызова `make test-db-init`).

---

## Архитектура проекта

```text
├── docker/             # Dockerfile (python + uv, nginx, postgres)
├── migrations/         # Миграции Alembic (асинхронный env.py)
├── src/
│   ├── api/            # Эндпоинты (v1) и зависимости (deps.py)
│   ├── core/           # Конфигурация (Pydantic Settings), БД, Redis, JWT/Argon2, Loguru
│   ├── models/         # ORM-модели SQLAlchemy 2.0 (DeclarativeBase)
│   ├── schemas/        # DTO схемы Pydantic v2
│   ├── services/       # Бизнес-логика приложения
│   └── main.py         # Входная точка FastAPI (lifespan, CORS, health)
├── tests/              # Интеграционные тесты с реальным Postgres/Redis
├── compose.yaml        # Оркестрация сервисов
├── Makefile            # Автоматизация команд
└── pyproject.toml      # Зависимости и настройки линтеров (Ruff, Pytest)
```
