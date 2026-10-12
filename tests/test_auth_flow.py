"""Тесты флоу аутентификации REST API: регистрация, логин, аудит и /auth/me."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AuditEvent, User


@pytest.mark.asyncio
async def test_register_weak_password_rejected(client: AsyncClient) -> None:
    """Проверяет, что регистрация со слабым паролем возвращает ошибку 400."""
    response = await client.post(
        "/auth/register",
        json={"email": "weak_user@example.com", "password": "123"},
    )
    assert response.status_code == 400
    assert "не менее" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_register_success(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Проверяет регистрацию пользователя и фиксацию аудита user.created."""
    email = "new_registered@example.com"
    password = "SuperSecurePassword123!"

    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Проверяем появление пользователя в базе
    user_res = await db_session.execute(select(User).where(User.email == email))
    user = user_res.scalar_one_or_none()
    assert user is not None

    # Проверяем запись события аудита
    audit_res = await db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == "user.created",
            AuditEvent.actor_id == user.id,
        )
    )
    audit_event = audit_res.scalar_one_or_none()
    assert audit_event is not None


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    """Проверяет ошибку 409 Conflict при повторной регистрации email."""
    email = "duplicate_check@example.com"
    password = "MyComplexPassword123!"

    res1 = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert res1.status_code in (200, 201)

    res2 = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert res2.status_code == 409
    assert "уже зарегистрирован" in res2.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_401(client: AsyncClient) -> None:
    """
    Проверяет ошибку 401 при неверных учетных данных.

    Возвращает нейтральное сообщение без раскрытия конкретного поля.
    """
    response = await client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    detail = response.json().get("detail", "")
    assert detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_success_and_audit_event(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    Проверяет успешный логин и запись аудита.

    Получает access_token и проверяет событие 'user.login.success'.
    """
    email = "login_success@example.com"
    password = "MyComplexPassword123!"

    # Сначала регистрируем
    reg_res = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert reg_res.status_code in (200, 201)

    # Выполняем вход
    login_res = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token

    # Проверяем событие user.login.success в audit_events
    audit_res = await db_session.execute(
        select(AuditEvent)
        .where(AuditEvent.event_type == "user.login.success")
        .order_by(AuditEvent.id.desc())
    )
    audit_event = audit_res.scalars().first()
    assert audit_event is not None
    assert audit_event.metadata_json is not None
    assert audit_event.metadata_json.get("email") == email


@pytest.mark.asyncio
async def test_auth_me_unauthorized(client: AsyncClient) -> None:
    """Проверяет, что GET /auth/me без токена возвращает 401 Unauthorized."""
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_with_token(client: AsyncClient) -> None:
    """Проверяет получение данных текущего пользователя по Bearer-токену."""
    email = "me_tester@example.com"
    password = "MyComplexPassword123!"

    reg_res = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    token = reg_res.json()["access_token"]

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "is_admin" in data
