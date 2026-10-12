"""Модель аудита событий."""

from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins import CreatedAtMixin, IntPKMixin


class AuditEvent(Base, IntPKMixin, CreatedAtMixin):
    """
    Запись о событии, сохраненная для аудита.

    Attributes:
        event_type: Тип события.
        actor_id: Идентификатор пользователя, вызвавшего событие.
        client_id: Идентификатор OAuth-клиента, если событие с ним связано.
        ip: IP-адрес источника события, если известен.
        user_agent: User-Agent клиента, если известен.
        metadata_json: Дополнительные данные события.

    """

    __tablename__ = "audit_events"
    event_type: Mapped[str] = mapped_column(
        index=True,
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    client_id: Mapped[str | None] = mapped_column(nullable=True)
    ip: Mapped[str | None] = mapped_column(nullable=True)
    user_agent: Mapped[str | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
