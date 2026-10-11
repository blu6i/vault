"""Точка входа в приложение FastAPI."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.core.config import settings
from src.core.logging import setup_logging
from src.core.postgres_client import async_db
from src.core.redis_client import async_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Управление жизненным циклом приложения (startup и shutdown)."""
    # 1. Инициализация логирования
    setup_logging()
    logger.info("Запуск приложения {}...", settings.app_name)

    # 2. Проверка доступности PostgreSQL
    db_healthy = await async_db.healthcheck()
    if db_healthy:
        logger.info("Подключение к PostgreSQL успешно установлено")
    else:
        logger.warning("Не удалось подключиться к PostgreSQL")

    # 3. Проверка доступности Redis
    try:
        await async_redis.set("healthcheck", "ok", ex=5)
        logger.info("Подключение к Redis успешно установлено")
    except Exception as e:  # noqa: BLE001
        logger.warning("Не удалось подключиться к Redis: {}", e)

    yield

    # 4. Graceful shutdown
    logger.info("Остановка приложения {}...", settings.app_name)
    await async_db.dispose()
    await async_redis.close()
    logger.info("Все соединения (БД и Redis) успешно закрыты")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)


@app.get("/health", tags=["Система"])
async def health_check() -> dict[str, str]:
    """Проверка жизнеспособности сервиса."""
    return {"status": "ok", "app": settings.app_name}
