"""Базовый декларативный класс для моделей SQLAlchemy."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей проекта."""

    metadata = MetaData(naming_convention=settings.db.naming_convention)
