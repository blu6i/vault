"""Объектные типы (ObjectType) для маппинга полей GraphQL на модели данных."""

from typing import Any

from ariadne import ObjectType
from ariadne.types import GraphQLResolveInfo

from src.models import AuditEvent, OAuthClient, User

client_type = ObjectType("Client")


@client_type.field("clientName")
def resolve_client_name(client: OAuthClient, info: GraphQLResolveInfo) -> str:  # noqa: ARG001
    """Резолвер отображаемого имени клиента для фронтенда."""
    return client.name


@client_type.field("redirectUris")
def resolve_client_redirect_uris(
    client: OAuthClient,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> list[str]:
    """Резолвер списка redirect_uris."""
    return client.redirect_uris or []


@client_type.field("isConfidential")
def resolve_client_is_confidential(
    client: OAuthClient,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> bool:
    """Резолвер флага конфиденциальности клиента."""
    return client.is_confidential


@client_type.field("clientId")
def resolve_client_id_field(
    client: OAuthClient,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> str:
    """Резолвер client_id."""
    return client.client_id


user_type = ObjectType("User")


@user_type.field("isActive")
def resolve_user_is_active(user: User, info: GraphQLResolveInfo) -> bool:  # noqa: ARG001
    """Резолвер статуса активности пользователя."""
    return user.is_active


@user_type.field("isAdmin")
def resolve_user_is_admin(user: User, info: GraphQLResolveInfo) -> bool:  # noqa: ARG001
    """Резолвер статуса администратора пользователя."""
    return user.is_admin


audit_event_type = ObjectType("AuditEvent")


@audit_event_type.field("eventType")
def resolve_audit_event_type(
    event: AuditEvent,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> str:
    """Резолвер типа события."""
    return event.event_type


@audit_event_type.field("actorId")
def resolve_audit_actor_id(
    event: AuditEvent,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> int | None:
    """Резолвер actor_id."""
    return event.actor_id


@audit_event_type.field("clientId")
def resolve_audit_client_id(
    event: AuditEvent,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> str | None:
    """Резолвер client_id события."""
    return event.client_id


@audit_event_type.field("metadata")
def resolve_audit_metadata(
    event: AuditEvent,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> dict[str, Any] | None:
    """Резолвер метаданных события из metadata_json."""
    return event.metadata_json


auth_payload_type = ObjectType("AuthPayload")


@auth_payload_type.field("accessToken")
def resolve_auth_access_token(
    payload: Any,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> str:
    """Резолвер access_token."""
    if isinstance(payload, dict):
        return str(payload.get("access_token", ""))
    return str(getattr(payload, "access_token", ""))


@auth_payload_type.field("tokenType")
def resolve_auth_token_type(
    payload: Any,
    info: GraphQLResolveInfo,  # noqa: ARG001
) -> str:
    """Резолвер token_type."""
    if isinstance(payload, dict):
        return str(payload.get("token_type", "bearer"))
    return str(getattr(payload, "token_type", "bearer"))
