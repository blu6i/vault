"""Тесты хеширования, верификации и политики сложности паролей."""

import pytest

from src.core.security import (
    WeakPasswordError,
    hash_password,
    validate_policy,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    """Проверяет создание корректного Argon2id хеша и его успешную верификацию."""
    raw_password = "SuperSecurePassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_weak_password_rejected() -> None:
    """Проверяет отклонение коротких и предсказуемых паролей (политика zxcvbn)."""
    # 1. Слишком короткий пароль (< min_length)
    with pytest.raises(WeakPasswordError, match="не менее"):
        validate_policy("12345")

    # 2. Банальный пароль
    with pytest.raises(WeakPasswordError):
        validate_policy("password123")

    # 3. Пароль, содержащий email пользователя
    with pytest.raises(WeakPasswordError):
        validate_policy("admin12345678", user_inputs=["admin@example.com", "admin"])


def test_strong_password_accepted() -> None:
    """Проверяет успешное прохождение валидации надежным паролем."""
    strong_pass = "V3ry$tr0ng&Complex!Pass2026"
    # Не должно выбрасывать исключений
    validate_policy(strong_pass, user_inputs=["user@example.com"])
