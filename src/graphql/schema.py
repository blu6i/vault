"""Сборка исполняемой GraphQL схемы и ASGI-приложения."""

from pathlib import Path

from ariadne import load_schema_from_path, make_executable_schema
from ariadne.asgi import GraphQL

from src.graphql.context import get_context_value
from src.graphql.directives import IsAdminDirective, IsAuthenticatedDirective
from src.graphql.resolvers import mutation, query
from src.graphql.scalars import datetime_scalar, json_scalar
from src.graphql.types import (
    audit_event_type,
    auth_payload_type,
    client_type,
    user_type,
)

# 1. Загрузка SDL-схемы из файла schema.graphql
schema_file_path = Path(__file__).parent / "schema.graphql"
type_defs = load_schema_from_path(str(schema_file_path))

# 2. Сборка исполняемой схемы
schema = make_executable_schema(
    type_defs,
    query,
    mutation,
    datetime_scalar,
    json_scalar,
    client_type,
    user_type,
    audit_event_type,
    auth_payload_type,
    directives={
        "isAuthenticated": IsAuthenticatedDirective,
        "isAdmin": IsAdminDirective,
    },
)

# 3. ASGI-приложение GraphQL с поддержкой GraphQL Playground
graphql_app = GraphQL(
    schema,
    context_value=get_context_value,
    debug=True,
)
