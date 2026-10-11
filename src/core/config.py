"""Настройки для проекта."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTToken(BaseModel):
    """Настройки для генерации и проверки JWT токенов."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_days: int = 30


class AuthSettings(BaseModel):
    """Настройки cookies авторизации."""

    cookie_name: str = "access_token"
    cookie_secure: bool = False  # True для production (HTTPS)
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None


class LogSettings(BaseModel):
    """Настройки для логера."""

    level: str = "INFO"
    rotation: str = "10 MB"
    retention: str = "14 days"
    dir: Path = Field(default=Path("logs"))
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{file}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )


class RedisSettings(BaseModel):
    """Настройки для подключения к Redis (кэш и сессии)."""

    host: str = "redis"
    port: int = 6379
    db: int = 0
    password: str | None = None

    @computed_field
    def url(self) -> str:
        """Ссылка для подключения к Redis."""
        password = f":{self.password}@" if self.password else ""
        return f"redis://{password}{self.host}:{self.port}/{self.db}"


class DBSettings(BaseModel):
    """Настройки для подключения к БД."""

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "app"
    postgres_user: str = "admin"
    postgres_password: str

    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @computed_field
    @property
    def url(self) -> str:
        """Ссылка для асинхронного подключения к БД."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class Cors(BaseModel):
    """Настройка CORS."""

    allowed_origins: list[str] = ["*"]
    allow_credentials: bool = False
    allow_methods: list[str] = [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ]
    allow_headers: list[str] = ["*"]


class Password(BaseModel):
    """Безопасность паролей."""

    pepper: str
    min_length: int = 8


class Settings(BaseSettings):
    """Все настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "my-python-app"
    debug: bool = False

    db: DBSettings
    log: LogSettings = LogSettings()
    redis: RedisSettings = RedisSettings()
    jwt: JWTToken
    auth: AuthSettings = AuthSettings()
    cors: Cors = Cors()
    password: Password


settings = Settings()  # type: ignore[call-arg]
