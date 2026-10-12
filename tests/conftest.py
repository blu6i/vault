"""Фикстуры Pytest для тестирования приложения (детерминированная проверка окружения)."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings
from src.core.postgres_client import async_db
from src.core.redis_client import RedisDatabase, get_async_redis
from src.main import app
from src.models.base import Base

TEST_DB_NAME = f"{settings.db.postgres_db}_test"

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.db.postgres_user}:{settings.db.postgres_password}@"
    f"{settings.db.postgres_host}:{settings.db.postgres_port}/{TEST_DB_NAME}"
)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def verify_test_environment() -> AsyncGenerator[None]:
    """
    Строго проверяет наличие базы данных и таблиц перед запуском тестов.

    Если окружение не подготовлено пользователем явно, тесты прерываются.
    """
    # 1. Проверяем доступность тестовой БД
    try:
        async with test_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(
            f"Тестовая база данных '{TEST_DB_NAME}' недоступна или не создана.\n"
            "Пожалуйста, выполните команду явной инициализации: make test-db-init"
        ) from e

    # 2. Проверяем наличие всех зарегистрированных таблиц
    async with test_engine.connect() as conn:

        def check_tables(sync_conn):
            inspector = inspect(sync_conn)
            existing_tables = set(inspector.get_table_names())
            expected_tables = set(Base.metadata.tables.keys())
            missing = expected_tables - existing_tables
            if missing:
                raise RuntimeError(
                    f"В тестовой БД отсутствуют таблицы: {missing}.\n"
                    "Пожалуйста, примените миграции: make test-db-init"
                )

        await conn.run_sync(check_tables)

    yield

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Изолированная сессия БД на каждый тест с откатом транзакции (Savepoint)."""
    orig_factory = async_db.session_factory
    async_db.session_factory = TestingSessionLocal

    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        yield session

        await transaction.rollback()
        await session.close()

    async_db.session_factory = orig_factory


@pytest_asyncio.fixture
async def fake_async_redis() -> AsyncGenerator[RedisDatabase]:
    """Асинхронный клиент Redis с префиксом test:."""
    test_redis = RedisDatabase(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        prefix="test",
    )
    yield test_redis

    try:
        keys = await test_redis.keys("*")
        for key in keys:
            await test_redis.delete(key)
    except Exception:  # noqa: BLE001
        pass
    await test_redis.close()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    fake_async_redis: RedisDatabase,
) -> AsyncGenerator[AsyncClient]:
    """HTTP-клиент для вызова эндпоинтов FastAPI с подменой боевой БД и Redis."""

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    async def override_get_redis() -> RedisDatabase:
        return fake_async_redis

    app.dependency_overrides[async_db.get_session] = override_get_db
    app.dependency_overrides[get_async_redis] = override_get_redis

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
