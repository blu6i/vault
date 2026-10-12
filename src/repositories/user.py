"""Репозиторий для операций аутентификации с пользователями."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AlreadyExistsException
from src.models import User


def _is_email_unique_violation(error: IntegrityError) -> bool:
    """Проверяет, вызвана ли ошибка ограничением уникальности email."""
    original_error = error.orig
    constraint_name = getattr(
        getattr(original_error, "diag", None),
        "constraint_name",
        None,
    )
    if constraint_name == "ix_users_email":
        return True

    return "unique constraint failed: users.email" in str(original_error).lower()


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
