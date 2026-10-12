"""Точка входа в приложение FastAPI."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.api.v1.auth import router as auth_router
from src.core.config import settings
from src.core.exceptions import AppException
from src.core.logging import setup_logging
from src.core.postgres_client import async_db
from src.core.redis_client import async_redis
from src.core.security import WeakPasswordError
from src.graphql.schema import graphql_app


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


@app.exception_handler(WeakPasswordError)
async def weak_password_handler(request: Request, exc: WeakPasswordError) -> JSONResponse:  # noqa: ARG001
    """Возвращает 400 Bad Request при несоблюдении политики сложности пароля."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:  # noqa: ARG001
    """Обрабатывает ошибки валидации Pydantic, возвращая 400 для паролей."""
    errors = exc.errors()
    for err in errors:
        msg = err.get("msg", "")
        if "Value error" in msg:
            clean_msg = msg.replace("Value error, ", "").strip()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": clean_msg},
            )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request, exc: AppException  # noqa: ARG001
) -> JSONResponse:
    """Обрабатывает предсказуемые доменные исключения приложения."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception  # noqa: ARG001
) -> JSONResponse:
    """Перехватывает любые непредвиденные ошибки и скрывает внутренний код и трейсбек."""
    logger.exception("Непредвиденная внутренняя ошибка сервера: {}", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """Обеспечивает наличие сессии БД в request.state для эндпоинтов и GraphQL."""
    if not hasattr(request.state, "db_session") or request.state.db_session is None:
        get_session_fn = app.dependency_overrides.get(
            async_db.get_session, async_db.get_session
        )
        async for session in get_session_fn():
            request.state.db_session = session
            return await call_next(request)
    return await call_next(request)


app.include_router(auth_router)
app.mount("/graphql", graphql_app)
app.mount("/admin", StaticFiles(directory="src/static", html=True), name="admin")

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
