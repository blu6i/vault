"""Первичные ключи."""

from sqlalchemy.orm import Mapped, mapped_column


class IntPKMixin:
    """Первичный ключ int."""

    id: Mapped[int] = mapped_column(primary_key=True)
