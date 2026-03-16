"""
Pydantic schemas for tag endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Request schemas ──


class TagCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")


# ── Response schemas ──


class TagResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TagWithCountResponse(TagResponse):
    entry_count: int = 0


class TagListResponse(BaseModel):
    tags: list[TagWithCountResponse]
