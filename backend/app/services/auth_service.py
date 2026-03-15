"""
Authentication service — business logic for registration, login, refresh, logout.
"""

import logging
import uuid
from datetime import UTC, datetime

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_access_token_expire_seconds,
    get_refresh_token_expires_at,
    hash_password,
    verify_password,
)
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import AuthResponse, TokenResponse, UserResponse

logger = logging.getLogger(__name__)


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str | None = None,
) -> AuthResponse:
    """Create a new user account and return tokens."""
    # Check for existing user
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("A user with this email already exists.")

    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
    )
    db.add(user)
    await db.flush()  # populate user.id

    tokens = await _create_session(db, user)
    logger.info("User registered: %s", user.id)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    device_info: str | None = None,
    ip_address: str | None = None,
) -> AuthResponse:
    """Authenticate user credentials and return tokens."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password.")

    tokens = await _create_session(db, user, device_info=device_info, ip_address=ip_address)
    logger.info("User logged in: %s", user.id)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


async def refresh_tokens(
    db: AsyncSession,
    refresh_token_str: str,
) -> TokenResponse:
    """Validate refresh token, revoke it, and issue a new pair (token rotation)."""
    try:
        payload = decode_token(refresh_token_str)
    except JWTError:
        raise UnauthorizedError("Invalid or expired refresh token.") from None

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type.")

    user_id = uuid.UUID(payload["sub"])

    # Find the active session with this refresh token
    result = await db.execute(
        select(Session).where(
            Session.user_id == user_id,
            Session.refresh_token == refresh_token_str,
            Session.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise UnauthorizedError("Refresh token not found or already revoked.")

    # Revoke old session
    session.revoked_at = datetime.now(UTC)

    # Create new session
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User not found.")

    tokens = await _create_session(db, user)
    logger.info("Tokens refreshed for user: %s", user_id)
    return tokens


async def logout_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    refresh_token_str: str,
) -> None:
    """Revoke the session associated with the given refresh token."""
    result = await db.execute(
        select(Session).where(
            Session.user_id == user_id,
            Session.refresh_token == refresh_token_str,
            Session.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if session is not None:
        session.revoked_at = datetime.now(UTC)
    logger.info("User logged out: %s", user_id)


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Fetch a user by primary key."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _create_session(
    db: AsyncSession,
    user: User,
    device_info: str | None = None,
    ip_address: str | None = None,
) -> TokenResponse:
    """Create a DB session record and return access + refresh tokens."""
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    session = Session(
        user_id=user.id,
        refresh_token=refresh_token,
        device_info=device_info,
        ip_address=ip_address,
        expires_at=get_refresh_token_expires_at(),
    )
    db.add(session)
    await db.flush()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=get_access_token_expire_seconds(),
    )
