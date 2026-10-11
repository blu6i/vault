"""Управление подключением и операциями с Redis."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast

import redis.asyncio as redis

from src.core.config import settings


class RedisDatabase:
    """Управляет пулом соединений и операциями с Redis."""

    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        password: str | None = None,
        prefix: str = "",
    ) -> None:
        self.prefix = prefix
        self._pool: redis.ConnectionPool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        self._client: redis.Redis = redis.Redis(connection_pool=self._pool)

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[redis.Redis]:
        """Предоставляет асинхронный контекстный менеджер для прямого доступа к Redis."""
        yield self._client

    async def close(self) -> None:
        """Закрывает клиент и отключает пул соединений (для lifespan shutdown)."""
        await self._client.aclose()
        await self._pool.disconnect()

    # ===== Хелперы для работы с префиксом =====

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}:{key}" if self.prefix else key

    async def set(
        self,
        key: str,
        value: Any,
        ex: int = 300,
        nx: bool = False,
    ) -> bool:
        """Асинхронно сохраняет значение ключа со сроком жизни (в секундах)."""
        result = await self._client.set(
            self._full_key(key),
            value,
            ex=ex,
            nx=nx,
        )
        return bool(result)

    async def get(self, key: str) -> str | None:
        """Асинхронно получает значение по ключу."""
        return cast(str | None, await self._client.get(self._full_key(key)))

    async def delete(self, key: str) -> int:
        """Асинхронно удаляет ключ."""
        return await self._client.delete(self._full_key(key))

    async def exists(self, key: str) -> bool:
        """Проверяет наличие ключа в Redis."""
        return bool(await self._client.exists(self._full_key(key)))

    async def keys(self, pattern: str = "*") -> list[str]:
        """Безопасный поиск ключей через SCAN (не блокирует Redis сервер)."""
        keys_list: list[str] = []
        async for key in self._client.scan_iter(
            match=self._full_key(pattern), count=100
        ):
            keys_list.append(key)
        return keys_list


# Глобальный инстанс фасада Redis
async_redis = RedisDatabase(
    host=settings.redis.host,
    port=settings.redis.port,
    db=settings.redis.db,
    password=settings.redis.password,
)


async def get_async_redis() -> RedisDatabase:
    """FastAPI зависимость (Dependency Injection) для инъекции фасада Redis."""
    return async_redis
