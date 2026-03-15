"""
Pydantic schemas for authentication endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ── Request schemas ──


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Response schemas ──


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
