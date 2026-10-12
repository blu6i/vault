"""Хэширование паролей и проверка политики их стойкости."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from zxcvbn import zxcvbn

from src.core.config import settings

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=19 * 1024,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


class WeakPasswordError(ValueError):
    """Возникает, если пароль не соответствует политике безопасности."""


def hash_password(password: str) -> str:
    """Создает Argon2id-хэш пароля с pepper из настроек."""
    return _password_hasher.hash(f"{password}{settings.password.pepper}")


def verify_password(password: str, hashed: str) -> bool:
    """Проверяет пароль и pepper против Argon2id-хэша."""
    try:
        return _password_hasher.verify(hashed, f"{password}{settings.password.pepper}")
    except VerificationError:
        return False


def validate_policy(
    password: str,
    user_inputs: Sequence[str] | None = None,
) -> None:
    """
    Проверяет минимальную длину и оценку стойкости пароля по алгоритму zxcvbn.

    Args:
        password: Сырой пароль пользователя.
        user_inputs: Список данных пользователя (логин, email, имя),
          которые недопустимы внутри пароля.

    Raises:
        WeakPasswordError: Если пароль короткий или легко подбирается.

    """
    min_length = settings.password.min_length
    if len(password) < min_length:
        raise WeakPasswordError(
            f"Пароль должен содержать не менее {min_length} символов."
        )

    # zxcvbn оценивает энтропию от 0 (очень слабый) до 4 (очень стойкий)
    result = zxcvbn(password, user_inputs=list(user_inputs or ()))
    if result["score"] < 3:
        # Извлекаем подсказку от zxcvbn, если она есть
        warning = result.get("feedback", {}).get("warning")
        msg = (
            f"Пароль слишком слабый: {warning}"
            if warning
            else "Пароль слишком легко угадать. Используйте более сложную комбинацию."
        )
        raise WeakPasswordError(msg)


# ==============================================================================
# Работа с JWT токенами
# ==============================================================================


def create_token(
    subject: str | int,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Базовая фабрика для создания подписанных JWT токенов."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )


def create_access_token(
    subject: str | int,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Создает короткоживущий Access токен."""
    expires_delta = timedelta(minutes=settings.jwt.access_token_expire_minutes)
    return create_token(
        subject=subject,
        token_type="access",
        expires_delta=expires_delta,
        additional_claims=additional_claims,
    )


def create_refresh_token(
    subject: str | int,
) -> str:
    """Создает долгоживущий Refresh токен."""
    expires_delta = timedelta(days=settings.jwt.refresh_token_expire_days)
    return create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=expires_delta,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Декодирует и проверяет валидность JWT токена."""
    return jwt.decode(
        token,
        settings.jwt.secret_key,
        algorithms=[settings.jwt.algorithm],
    )
