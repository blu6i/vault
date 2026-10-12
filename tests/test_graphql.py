"""Тесты GraphQL API: директивы @isAuthenticated и @isAdmin, мутации."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import create_user


@pytest.mark.asyncio
async def test_graphql_protected_field_without_token(client: AsyncClient) -> None:
    """Проверяет запрос me без токена: 'Authentication required'."""
    query = "{ me { id email } }"
    response = await client.post("/graphql/", json={"query": query})
    assert response.status_code == 400
    data = response.json()
    assert data.get("data") is None
    assert any(
        "Authentication required" in err["message"]
        for err in data.get("errors", [])
    )


@pytest.mark.asyncio
async def test_graphql_users_query_non_admin_fails(
    client: AsyncClient,
) -> None:
    """Проверяет запрос users обычным пользователем: 'Admin only'."""
    email = "regular_user@example.com"
    password = "SuperPassword123!"
    reg_res = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    token = reg_res.json()["access_token"]

    query = "{ users { id email isAdmin } }"
    response = await client.post(
        "/graphql/",
        json={"query": query},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data.get("data") is None
    assert any("Admin only" in err["message"] for err in data.get("errors", []))


@pytest.mark.asyncio
async def test_graphql_users_query_as_admin_succeeds(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Проверяет, что администратор может успешно получить список пользователей."""
    admin = await create_user(
        db_session,
        email="test_admin@example.com",
        password="SuperPassword123!",
        is_admin=True,
    )

    login_res = await client.post(
        "/auth/login",
        json={"email": admin.email, "password": "SuperPassword123!"},
    )
    token = login_res.json()["access_token"]

    query = "{ users { id email isAdmin } }"
    response = await client.post(
        "/graphql/",
        json={"query": query},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "users" in data["data"]
    assert len(data["data"]["users"]) >= 1


@pytest.mark.asyncio
async def test_graphql_create_client_and_query_clients(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Проверяет создание OAuth-клиента администратором и получение списка."""
    admin = await create_user(
        db_session,
        email="client_admin@example.com",
        password="SuperPassword123!",
        is_admin=True,
    )
    login_res = await client.post(
        "/auth/login",
        json={"email": admin.email, "password": "SuperPassword123!"},
    )
    token = login_res.json()["access_token"]

    mutation = """
    mutation CreateClient(
      $name: String!,
      $isConfidential: Boolean!,
      $redirectUris: [String!]
    ) {
      createClient(
        name: $name,
        isConfidential: $isConfidential,
        redirectUris: $redirectUris
      ) {
        id
        clientId
        name
        isConfidential
        redirectUris
      }
    }
    """
    mutation_vars = {
        "name": "Integration Test Client",
        "isConfidential": True,
        "redirectUris": ["http://localhost:8080/callback"],
    }

    create_res = await client.post(
        "/graphql/",
        json={"query": mutation, "variables": mutation_vars},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 200
    create_data = create_res.json()["data"]["createClient"]
    assert create_data["name"] == "Integration Test Client"
    assert create_data["isConfidential"] is True

    query = "{ clients { id name clientId isConfidential redirectUris } }"
    list_res = await client.post(
        "/graphql/",
        json={"query": query},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    clients_list = list_res.json()["data"]["clients"]
    assert any(c["name"] == "Integration Test Client" for c in clients_list)
