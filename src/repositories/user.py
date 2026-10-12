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
    hashed_password: str,
) -> User:
    """Создаёт пользователя."""
    user = User(email=email, hashed_password=hashed_password)
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
