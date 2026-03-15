"""
Authentication API endpoints.

POST /auth/register  — Create a new account
POST /auth/login     — Authenticate and get tokens
POST /auth/refresh   — Rotate refresh token
POST /auth/logout    — Revoke refresh token
GET  /auth/me        — Get current user profile
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    return await auth_service.register_user(
        db, email=body.email, password=body.password, display_name=body.display_name
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    device_info = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    return await auth_service.login_user(
        db, email=body.email, password=body.password, device_info=device_info, ip_address=ip_address
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await auth_service.refresh_tokens(db, refresh_token_str=body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await auth_service.logout_user(
        db, user_id=current_user.id, refresh_token_str=body.refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
