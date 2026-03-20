"""Unit tests for security utilities (password hashing and JWT)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_access_token_expire_seconds,
    get_refresh_token_expires_at,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_returns_bcrypt_string(self):
        hashed = hash_password("mysecret123")
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_correct_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("correct-password", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # different salts

    def test_unicode_password(self):
        hashed = hash_password("pässwörd123")
        assert verify_password("pässwörd123", hashed) is True


class TestJWT:
    def test_access_token_contains_correct_claims(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_refresh_token_contains_correct_claims(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload

    def test_access_token_is_not_refresh(self):
        token = create_access_token(uuid.uuid4())
        payload = decode_token(token)
        assert payload["type"] != "refresh"

    def test_decode_expired_token_raises(self):
        from jose import JWTError

        from app.config import settings

        payload = {
            "sub": str(uuid.uuid4()),
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        with pytest.raises(JWTError):
            decode_token(token)

    def test_decode_invalid_token_raises(self):
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_token("not-a-real-token")

    def test_get_access_token_expire_seconds(self):
        from app.config import settings

        expected = settings.jwt_access_token_expire_minutes * 60
        assert get_access_token_expire_seconds() == expected

    def test_get_refresh_token_expires_at_is_in_future(self):
        expires_at = get_refresh_token_expires_at()
        assert expires_at > datetime.now(UTC)
