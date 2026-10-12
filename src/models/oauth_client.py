"""Модель OAuth-клиентов."""

from sqlalchemy import JSON, false
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins import IntPKMixin, TimestampMixin


class OAuthClient(Base, IntPKMixin, TimestampMixin):
    """
    Зарегистрированный OAuth-клиент.

    Attributes:
        client_id: Уникальный идентификатор OAuth-клиента.
        name: Отображаемое имя приложения.
        is_confidential: Может ли клиент безопасно хранить секрет.
            По умолчанию False.
        redirect_uris: Список URI, на которые разрешено перенаправлять
            пользователя после авторизации.

    """

    __tablename__ = "oauth_clients"
    client_id: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        nullable=False,
    )
    is_confidential: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
        nullable=False,
    )
    redirect_uris: Mapped[list[str]] = mapped_column(JSON)
