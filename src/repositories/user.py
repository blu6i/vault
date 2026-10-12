"""Репозиторий для операций аутентификации с пользователями."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AlreadyExistsException
from src.models import User


def _is_email_unique_violation(error: IntegrityError) -> bool:
    """Проверяет, вызвана ли ошибка ограничением уникальности email."""
    orig = getattr(error, "orig", None)

    # 1. asyncpg (driver_exception.constraint_name)
    driver_exc = getattr(orig, "driver_exception", None)
    if driver_exc is not None:
        constraint = getattr(driver_exc, "constraint_name", None)
        if constraint and "ix_users_email" in constraint:
            return True

    # 2. psycopg2 (orig.diag.constraint_name)
    diag = getattr(orig, "diag", None)
    if diag is not None:
        constraint = getattr(diag, "constraint_name", None)
        if constraint and "ix_users_email" in constraint:
            return True

    # 3. Прямой constraint_name у оригинальной ошибки
    constraint = getattr(orig, "constraint_name", None)
    if constraint and "ix_users_email" in constraint:
        return True

    # 4. Текстовый поиск в тексте ошибки (SQLite, asyncpg message, etc.)
    err_str = str(error).lower()
    return (
        "ix_users_email" in err_str
        or "unique constraint failed: users.email" in err_str
        or "users_email_key" in err_str
        or "users.email" in err_str
    )


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    hashed_password: str | None = None,
    password: str | None = None,
    is_admin: bool = False,
    is_active: bool = True,
) -> User:
    """Создаёт пользователя."""
    from src.core.security import hash_password

    final_hash = hashed_password or (hash_password(password) if password else "")
    user = User(
        email=email,
        hashed_password=final_hash,
        is_admin=is_admin,
        is_active=is_active,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as error:
        await session.rollback()
        if _is_email_unique_violation(error):
            raise AlreadyExistsException from error
        raise

    await session.commit()
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Находит пользователя по email."""
    return await session.scalar(select(User).where(User.email == email))
