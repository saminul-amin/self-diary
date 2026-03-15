"""
FastAPI dependency injection functions.

Provides:
- get_db: Yields an async database session
- get_current_user: Decodes JWT and returns the authenticated user
"""

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.db.database import get_db  # noqa: F401 — re-exported for convenience
from app.models.user import User
from app.services.auth_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the JWT Bearer token and return the authenticated user."""
    if credentials is None:
        raise UnauthorizedError()

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token.") from None

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type.")

    user_id = uuid.UUID(payload["sub"])
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("User not found.")
    return user
