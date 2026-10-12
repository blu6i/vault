"""Провайдер контекста для выполнения GraphQL-запросов."""

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import extract_client_info
from src.core.postgres_client import async_db
from src.core.security import decode_token
from src.models import User

extract_request_client_info = extract_client_info


async def get_context_value(
    request: Request,
    data: Any = None,  # noqa: ARG001
) -> dict[str, Any]:
    """
    Формирует контекст GraphQL-запроса.

    Включает сессию SQLAlchemy (db, db_session), текущего пользователя
    (user, current_user) и HTTP-запрос (request).
    """
    session: AsyncSession = async_db.session_factory()
    request.state.db_session = session

    current_user: User | None = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
            if payload.get("type") == "access" and (user_id := payload.get("sub")):
                current_user = await session.get(User, int(user_id))
        except Exception:
            current_user = None

    return {
        "request": request,
        "db": session,
        "user": current_user,
    }
