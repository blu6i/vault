"""Модель пользователя."""

from sqlalchemy import false, true
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins import IntPKMixin, TimestampMixin


class User(Base, IntPKMixin, TimestampMixin):
    """
    Класс модели пользователя.

    Attributes :
        email (str): почта пользователя, обязательно поле.
        hashed_password (str): хэш пароля пользователя.
        is_active (bool): флаг активности пользователя. Заполняется True по умолчанию.
        is_admin (bool): флаг прав админа. Заполняется False по умопчанию.
    """

    __tablename__ = "users"
    email: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        server_default=true(),
        nullable=False,
    )
    is_admin: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
        nullable=False,
    )
