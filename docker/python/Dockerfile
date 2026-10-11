# 1. Забираем бинарник uv из официального образа
FROM ghcr.io/astral-sh/uv:latest AS uv_bin

# 2. Основной образ Python 3.14 (slim на базе Debian)
FROM python:3.14-slim-bookworm

# Аргументы для совпадения прав с пользователем хоста
ARG UID=1000
ARG GID=1000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/app/.venv/bin:$PATH"

# Системные утилиты (curl для healthcheck, procps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Копируем uv
COPY --from=uv_bin /uv /uvx /bin/

# Создаём пользователя app с UID/GID хоста
RUN groupadd -g "${GID}" -o app && \
    useradd -u "${UID}" -g app -m -s /bin/bash app

WORKDIR /app

# Переключаемся на непривилегированного пользователя
USER app

# Порт ASGI-сервера (Uvicorn)
EXPOSE 8000

# Запуск Uvicorn в режиме dev (--reload)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]