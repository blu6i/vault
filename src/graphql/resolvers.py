"""Резолверы для GraphQL Query и Mutation операций."""

import asyncio
import uuid
from typing import Any

from ariadne import MutationType, QueryType
from ariadne.types import GraphQLError, GraphQLResolveInfo  # type: ignore
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import extract_client_info
from src.core.exceptions import AlreadyExistsException
from src.core.security import (
    WeakPasswordError,
    create_access_token,
    hash_password,
    validate_policy,
)
from src.models import AuditEvent, OAuthClient, User
from src.repositories import create_user, get_user_by_email, write_event

query = QueryType()
mutation = MutationType()


# ==============================================================================
# Query Resolvers
# ==============================================================================


@query.field("me")
async def resolve_me(
    obj: Any,  # noqa: ARG001
    info: GraphQLResolveInfo,
) -> User:
    """Возвращает профиль текущего аутентифицированного пользователя."""
    user: User | None = info.context.get("user")
    if user is None:
        raise GraphQLError("Authentication required")
    return user


@query.field("users")
async def resolve_users(
    obj: Any,  # noqa: ARG001
    info: GraphQLResolveInfo,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[User]:
    """Возвращает список пользователей с опциональным поиском по email."""
    session: AsyncSession = info.context["db"]
    stmt = select(User).order_by(User.id.asc()).offset(offset).limit(limit)
    if search and search.strip():
        stmt = stmt.where(User.email.ilike(f"%{search.strip()}%"))
    result = await session.scalars(stmt)
    return list(result.all())


@query.field("clients")
async def resolve_clients(
    obj: Any,  # noqa: ARG001
    info: GraphQLResolveInfo,
) -> list[OAuthClient]:
    """Возвращает список зарегистрированных OAuth-клиентов."""
    session: AsyncSession = info.context["db"]
    stmt = select(OAuthClient).order_by(OAuthClient.id.asc())
    result = await session.scalars(stmt)
    return list(result.all())


@query.field("auditEvents")
async def resolve_audit_events(
    obj: Any,  # noqa: ARG001
    info: GraphQLResolveInfo,
    event_type: str | None = None,
    eventType: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditEvent]:
    """Возвращает журнал событий аудита с фильтрацией по типу события."""
    session: AsyncSession = info.context["db"]
    filter_type = event_type or eventType
    stmt = (
        select(AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if filter_type and filter_type.strip():
        stmt = stmt.where(AuditEvent.event_type == filter_type.strip())
    result = await session.scalars(stmt)
    return list(result.all())


# ==============================================================================
# Mutation Resolvers
# ==============================================================================


@mutation.field("registerUser")
async def resolve_register_user(
    obj: Any,  # noqa: ARG001
    info: GraphQLResolveInfo,
    email: str,
    password: str,
) -> dict[str, str]:
    """Регистрирует нового пользователя через GraphQL."""
    session: AsyncSession = info.context["db"]
    request = info.context.get("request")
    ip, user_agent = extract_client_info(request) if request else (None, None)

    try:
        validate_policy(password, user_inputs=[email])
    except WeakPasswordError as e:
        raise GraphQLError(str(e)) from e

    existing_user = await get_user_by_email(session, email)
    if existing_user is not None:
        await write_event(
            session,
            event_type="user.created.failure",
            actor_id=None,
            client_id=None,
            ip=ip,
            user_agent=user_agent,
            metadata={"email": email, "reason": "already_exists"},
        )
        raise GraphQLError("Пользователь с текущей почтой уже зарегистрирован.")

    hashed_pass = await asyncio.to_thread(hash_password, password)
    try:
        user = await create_user(session, email=email, hashed_password=hashed_pass)
        await write_event(
            session,
            event_type="user.created",
            actor_id=user.id,
            client_id=None,
            ip=ip,
            user_agent=user_agent,
            metadata={"email": user.email},
        )
    except AlreadyExistsException as e:
        raise GraphQLError("Пользователь с текущей почтой уже зарегистрирован.") from e

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@mutation.field("createClient")
async def resolve_create_client(
    obj: Any,  # noqa: ARG001
    info: GraphQLResolveInfo,
    name: str | None = None,
    is_confidential: bool | None = None,
    isConfidential: bool | None = None,
    redirect_uris: list[str] | None = None,
    redirectUris: list[str] | None = None,
    input: dict[str, Any] | None = None,
) -> OAuthClient:
    """Создаёт нового OAuth-клиента и записывает событие аудита."""
    session: AsyncSession = info.context["db"]
    request = info.context.get("request")
    current_user: User | None = info.context.get("user")
    ip, user_agent = extract_client_info(request) if request else (None, None)

    inp = input or {}
    client_name = inp.get("name") or name
    if not client_name or not client_name.strip():
        raise GraphQLError("Client name is required")

    confidential = (
        inp.get("is_confidential")
        if "is_confidential" in inp
        else (
            is_confidential
            if is_confidential is not None
            else (isConfidential if isConfidential is not None else False)
        )
    )
    uris = (
        inp.get("redirect_uris")
        if "redirect_uris" in inp
        else (
            redirect_uris
            if redirect_uris is not None
            else (redirectUris if redirectUris is not None else [])
        )
    )

    client = OAuthClient(
        client_id=str(uuid.uuid4()),
        name=client_name.strip(),
        is_confidential=bool(confidential),
        redirect_uris=uris,
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)

    await write_event(
        session,
        event_type="client.created",
        actor_id=current_user.id if current_user else None,
        client_id=client.client_id,
        ip=ip,
        user_agent=user_agent,
        metadata={"client_id": client.client_id, "name": client.name},
    )
    return client


@mutation.field("disableUser")
async def resolve_disable_user(
    obj: Any,  # noqa: ARG001
    info: GraphQLResolveInfo,
    user_id: Any = None,
    userId: Any = None,
) -> User:
    """Деактивирует пользователя по ID."""
    session: AsyncSession = info.context["db"]
    request = info.context.get("request")
    current_user: User | None = info.context.get("user")
    ip, user_agent = extract_client_info(request) if request else (None, None)

    raw_id = user_id or userId
    if raw_id is None:
        raise GraphQLError("userId is required")

    try:
        target_id = int(raw_id)
    except (ValueError, TypeError) as e:
        raise GraphQLError("Invalid userId") from e

    target_user = await session.get(User, target_id)
    if target_user is None:
        raise GraphQLError(f"User with ID {target_id} not found")

    target_user.is_active = False
    await session.commit()
    await session.refresh(target_user)

    await write_event(
        session,
        event_type="user.disabled",
        actor_id=current_user.id if current_user else None,
        client_id=None,
        ip=ip,
        user_agent=user_agent,
        metadata={"disabled_user_id": target_user.id, "email": target_user.email},
    )
    return target_user
