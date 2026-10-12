"""Схема пользователя."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from src.core.security import validate_policy


class UserBase(BaseModel):
    """
    Базовая модель пользователя.

    Attributes:
        email (EmailStr): почта пользователя

    """

    email: EmailStr


class UserRead(UserBase):
    """
    Схема для чтения.

    Attributes:
        id (int): индификатор пользователя
        email (EmailStr): почта пользователя
        is_active (bool): флаг активности пользователя
        is_admin (bool): флаг прав админа
        created_at (datetime): дата-время создания

    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime


class UserRegister(UserBase):
    """
    Схема пользователя для регистрации.

    Attributes:
        email (EmailStr): почта пользователя
        password (str): пароль пользователя

    """

    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        """
        Проверка пароля.

        Args:
            value (str): пароль

        Returns:
            str: пароль

        """
        validate_policy(value)
        return value


class UserLogin(UserBase):
    """
    Схема пользователя для входа.

    Attributes:
        email (EmailStr): почта пользователя
        password (str): пароль пользователя

    """

    password: str
