"""Директивы безопасности для схемы GraphQL."""

import inspect
from typing import Any

from ariadne import SchemaDirectiveVisitor
from ariadne.types import GraphQLError, GraphQLResolveInfo  # type: ignore


class IsAuthenticatedDirective(SchemaDirectiveVisitor):
    """
    Директива @isAuthenticated.

    Оборачивает оригинальный резолвер поля: если в контексте нет user,
    выбрасывает исключение с сообщением 'Authentication required'.
    """

    def visit_field_definition(
        self,
        field: Any,
        object_type: Any,  # noqa: ARG002
    ) -> Any:
        """Оборачивает резолвер поля проверкой наличия пользователя."""
        original_resolve = getattr(field, "resolve", None)

        async def resolve_is_authenticated(
            obj: Any,
            info: GraphQLResolveInfo,
            **kwargs: Any,
        ) -> Any:
            user = info.context.get("user")
            if not user:
                raise GraphQLError("Authentication required")

            if original_resolve:
                result = original_resolve(obj, info, **kwargs)
                if inspect.isawaitable(result):
                    return await result
                return result
            return getattr(obj, info.field_name, None)

        field.resolve = resolve_is_authenticated
        return field


class IsAdminDirective(SchemaDirectiveVisitor):
    """
    Директива @isAdmin.

    Оборачивает оригинальный резолвер поля: если в контексте нет user,
    выбрасывает 'Authentication required'; если user.is_admin != True,
    выбрасывает 'Admin only'.
    """

    def visit_field_definition(
        self,
        field: Any,
        object_type: Any,  # noqa: ARG002
    ) -> Any:
        """Оборачивает резолвер поля проверкой прав администратора."""
        original_resolve = getattr(field, "resolve", None)

        async def resolve_is_admin(
            obj: Any,
            info: GraphQLResolveInfo,
            **kwargs: Any,
        ) -> Any:
            user = info.context.get("user")
            if not user:
                raise GraphQLError("Authentication required")
            if not getattr(user, "is_admin", False):
                raise GraphQLError("Admin only")

            if original_resolve:
                result = original_resolve(obj, info, **kwargs)
                if inspect.isawaitable(result):
                    return await result
                return result
            return getattr(obj, info.field_name, None)

        field.resolve = resolve_is_admin
        return field
