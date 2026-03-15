"""
Integration tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient

TEST_USER = {
    "email": "test@example.com",
    "password": "securepassword123",
    "display_name": "Test User",
}


@pytest.mark.asyncio
async def test_register(client: AsyncClient) -> None:
    resp = await client.post("/v1/auth/register", json=TEST_USER)
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == TEST_USER["email"]
    assert data["user"]["display_name"] == TEST_USER["display_name"]
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]
    assert data["tokens"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    await client.post("/v1/auth/register", json=TEST_USER)
    resp = await client.post("/v1/auth/register", json=TEST_USER)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/register",
        json={"email": "short@example.com", "password": "123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/register",
        json={"email": "not-an-email", "password": "securepassword123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login(client: AsyncClient) -> None:
    await client.post("/v1/auth/register", json=TEST_USER)
    resp = await client.post(
        "/v1/auth/login",
        json={"email": TEST_USER["email"], "password": TEST_USER["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == TEST_USER["email"]
    assert "access_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post("/v1/auth/register", json=TEST_USER)
    resp = await client.post(
        "/v1/auth/login",
        json={"email": TEST_USER["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient) -> None:
    reg = await client.post("/v1/auth/register", json=TEST_USER)
    token = reg.json()["tokens"]["access_token"]

    resp = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == TEST_USER["email"]


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient) -> None:
    resp = await client.get("/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient) -> None:
    resp = await client.get("/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient) -> None:
    reg = await client.post("/v1/auth/register", json=TEST_USER)
    refresh_token = reg.json()["tokens"]["refresh_token"]

    resp = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New refresh token should be different (rotation)
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_reuse_revoked(client: AsyncClient) -> None:
    """After refresh, the old token should be revoked."""
    reg = await client.post("/v1/auth/register", json=TEST_USER)
    old_refresh = reg.json()["tokens"]["refresh_token"]

    # Use it once
    await client.post("/v1/auth/refresh", json={"refresh_token": old_refresh})

    # Try to reuse — should fail
    resp = await client.post("/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient) -> None:
    resp = await client.post("/v1/auth/refresh", json={"refresh_token": "bad.token.here"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    reg = await client.post("/v1/auth/register", json=TEST_USER)
    tokens = reg.json()["tokens"]

    resp = await client.post(
        "/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 204

    # Refresh with the revoked token should fail
    resp = await client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_no_auth(client: AsyncClient) -> None:
    resp = await client.post("/v1/auth/logout", json={"refresh_token": "any"})
    assert resp.status_code == 401
