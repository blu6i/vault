"""Кастомные скалярные типы для GraphQL схемы."""

from datetime import datetime
from typing import Any

from ariadne import ScalarType

datetime_scalar = ScalarType("DateTime")


@datetime_scalar.serializer
def serialize_datetime(value: Any) -> str:
    """Сериализует объект datetime в строку стандарта ISO 8601."""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@datetime_scalar.value_parser
def parse_datetime_value(value: Any) -> datetime:
    """Парсит строку стандарта ISO 8601 в объект datetime."""
    return datetime.fromisoformat(value)


json_scalar = ScalarType("JSON")


@json_scalar.serializer
def serialize_json(value: Any) -> Any:
    """Сериализует значение JSON."""
    return value


@json_scalar.value_parser
def parse_json_value(value: Any) -> Any:
    """Парсит значение JSON."""
    return value
