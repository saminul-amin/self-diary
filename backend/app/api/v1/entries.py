"""
Diary entry API endpoints.

POST   /entries          — Create a new entry
GET    /entries          — List entries (paginated, filtered)
GET    /entries/search   — Search entries by text
GET    /entries/{id}     — Get a single entry
PUT    /entries/{id}     — Update an entry
DELETE /entries/{id}     — Soft-delete an entry
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.entry import Mood
from app.models.user import User
from app.schemas.entry import (
    EntryCreateRequest,
    EntryListParams,
    EntryListResponse,
    EntryResponse,
    EntryUpdateRequest,
)
from app.services import entry_service

router = APIRouter()


@router.post("", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    body: EntryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntryResponse:
    return await entry_service.create_entry(db, user_id=current_user.id, data=body)


@router.get("", response_model=EntryListResponse)
async def list_entries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    mood: Mood | None = Query(default=None),
    is_favorite: bool | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    updated_since: datetime | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntryListResponse:
    params = EntryListParams(
        page=page,
        page_size=page_size,
        mood=mood,
        is_favorite=is_favorite,
        date_from=date_from,
        date_to=date_to,
        updated_since=updated_since,
    )
    return await entry_service.list_entries(db, user_id=current_user.id, params=params)


@router.get("/search", response_model=EntryListResponse)
async def search_entries(
    q: str = Query(min_length=1, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntryListResponse:
    return await entry_service.search_entries(
        db, user_id=current_user.id, query=q, page=page, page_size=page_size
    )


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntryResponse:
    return await entry_service.get_entry(db, user_id=current_user.id, entry_id=entry_id)


@router.put("/{entry_id}", response_model=EntryResponse)
async def update_entry(
    entry_id: uuid.UUID,
    body: EntryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EntryResponse:
    return await entry_service.update_entry(
        db, user_id=current_user.id, entry_id=entry_id, data=body
    )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await entry_service.delete_entry(db, user_id=current_user.id, entry_id=entry_id)
