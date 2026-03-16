"""
Pydantic schemas for diary entry endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.entry import Mood
from app.schemas.tag import TagResponse

# ── Request schemas ──


class EntryCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    body: str = Field(min_length=1)
    mood: Mood | None = None
    is_favorite: bool = False
    client_id: uuid.UUID | None = None
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class EntryUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    body: str | None = Field(default=None, min_length=1)
    mood: Mood | None = None
    is_favorite: bool | None = None
    expected_version: int = Field(ge=1)
    tag_ids: list[uuid.UUID] | None = None


# ── Query schemas ──


class EntryListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    mood: Mood | None = None
    is_favorite: bool | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    updated_since: datetime | None = None


# ── Response schemas ──


class EntryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    body: str
    mood: Mood | None
    is_favorite: bool
    version: int
    client_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class EntryListResponse(BaseModel):
    entries: list[EntryResponse]
    page: int
    page_size: int
    total: int


class SearchResultItem(BaseModel):
    entry: EntryResponse
    headline: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    page: int
    page_size: int
    total: int
