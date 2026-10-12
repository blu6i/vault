"""Схема токена."""

from datetime import datetime

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """
    Схема отправки access токена и типа.

    Attributes:
        access_token (str): access токен
        token_type (str): тип токена. По умолчанию "bearer"

    """

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Нагрузка токена.

    Attributes:
        sub (str): владелец токена
        type (str): тип токена
        exp (datetime | int): жизнь токена
        jti (str): ИД токена
        iat (datetime | int): время слздания токена

    """

    sub: str
    type: str
    exp: datetime | int
    jti: str
    iat: datetime | int
