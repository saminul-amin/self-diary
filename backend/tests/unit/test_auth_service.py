"""Unit tests for auth service business logic."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ConflictError, UnauthorizedError
from app.services.auth_service import (
    get_user_by_id,
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
)


def _make_user(email="test@example.com", user_id=None, password_hash=None):
    """Create a mock User object."""
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = email
    user.password_hash = password_hash or "hashed"
    user.display_name = "Test User"
    user.avatar_url = None
    user.created_at = MagicMock()
    user.updated_at = MagicMock()
    return user


def _mock_scalar_one_or_none(value):
    """Return a mock execute result that yields `value` from scalar_one_or_none."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_register_raises_conflict_on_duplicate_email(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(_make_user())

        with pytest.raises(ConflictError, match="email already exists"):
            await register_user(db, "existing@test.com", "password123")

    @pytest.mark.asyncio
    async def test_register_creates_user_and_session(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        with (
            patch("app.services.auth_service.hash_password", return_value="hashed_pw"),
            patch("app.services.auth_service.create_access_token", return_value="access_tok"),
            patch("app.services.auth_service.create_refresh_token", return_value="refresh_tok"),
            patch("app.services.auth_service.get_access_token_expire_seconds", return_value=1800),
            patch("app.services.auth_service.get_refresh_token_expires_at"),
            patch("app.services.auth_service.UserResponse") as mock_user_resp_cls,
            patch("app.services.auth_service.AuthResponse") as mock_auth_cls,
        ):
            mock_user_resp_cls.model_validate.return_value = MagicMock()
            mock_auth = MagicMock()
            mock_auth.tokens.access_token = "access_tok"
            mock_auth.tokens.refresh_token = "refresh_tok"
            mock_auth_cls.return_value = mock_auth
            result = await register_user(db, "new@test.com", "password123", "New User")

        assert result.tokens.access_token == "access_tok"
        assert result.tokens.refresh_token == "refresh_tok"
        assert db.add.call_count == 2  # User + Session
        assert db.flush.call_count == 2


class TestLoginUser:
    @pytest.mark.asyncio
    async def test_login_raises_on_unknown_email(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        with pytest.raises(UnauthorizedError, match="Invalid email or password"):
            await login_user(db, "unknown@test.com", "password")

    @pytest.mark.asyncio
    async def test_login_raises_on_wrong_password(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(_make_user())

        with (
            patch("app.services.auth_service.verify_password", return_value=False),
            pytest.raises(UnauthorizedError, match="Invalid email or password"),
        ):
            await login_user(db, "test@test.com", "wrong-password")

    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self):
        user = _make_user()
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(user)

        with (
            patch("app.services.auth_service.verify_password", return_value=True),
            patch("app.services.auth_service.create_access_token", return_value="access_tok"),
            patch("app.services.auth_service.create_refresh_token", return_value="refresh_tok"),
            patch("app.services.auth_service.get_access_token_expire_seconds", return_value=1800),
            patch("app.services.auth_service.get_refresh_token_expires_at"),
        ):
            result = await login_user(db, "test@test.com", "correct-pw")

        assert result.tokens.access_token == "access_tok"


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_refresh_raises_on_invalid_token(self):
        db = AsyncMock()
        with (
            patch(
                "app.services.auth_service.decode_token",
                side_effect=__import__("jose").JWTError(),
            ),
            pytest.raises(UnauthorizedError, match="Invalid or expired refresh token"),
        ):
            await refresh_tokens(db, "bad-token")

    @pytest.mark.asyncio
    async def test_refresh_raises_on_wrong_token_type(self):
        db = AsyncMock()
        with (
            patch(
                "app.services.auth_service.decode_token",
                return_value={"sub": str(uuid.uuid4()), "type": "access"},
            ),
            pytest.raises(UnauthorizedError, match="Invalid token type"),
        ):
            await refresh_tokens(db, "access-token-not-refresh")

    @pytest.mark.asyncio
    async def test_refresh_raises_when_session_not_found(self):
        db = AsyncMock()
        user_id = uuid.uuid4()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        with (
            patch(
                "app.services.auth_service.decode_token",
                return_value={"sub": str(user_id), "type": "refresh"},
            ),
            pytest.raises(UnauthorizedError, match="not found or already revoked"),
        ):
            await refresh_tokens(db, "valid-refresh-token")


class TestLogoutUser:
    @pytest.mark.asyncio
    async def test_logout_revokes_session(self):
        session = MagicMock()
        session.revoked_at = None
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(session)

        await logout_user(db, uuid.uuid4(), "refresh-token")
        assert session.revoked_at is not None

    @pytest.mark.asyncio
    async def test_logout_no_op_when_session_missing(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        # Should not raise
        await logout_user(db, uuid.uuid4(), "missing-token")


class TestGetUserById:
    @pytest.mark.asyncio
    async def test_returns_user_when_found(self):
        user = _make_user()
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(user)

        result = await get_user_by_id(db, user.id)
        assert result is user

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        result = await get_user_by_id(db, uuid.uuid4())
        assert result is None
