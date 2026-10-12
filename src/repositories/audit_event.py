"""Репозиторий для аудиторских событий."""

from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AuditEvent


async def create_audit_event(
    session: AsyncSession,
    event_type: str,
    *,
    actor_id: int | None = None,
    client_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Создаёт запись аудита события."""
    audit_event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        client_id=client_id,
        ip=ip,
        user_agent=user_agent,
        metadata_json=metadata,
    )
    session.add(audit_event)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception("Ошибка при записи аудита.")


write_event = create_audit_event
