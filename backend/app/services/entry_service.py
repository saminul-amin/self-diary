"""
Diary entry service — business logic for entry CRUD and search.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.entry import Entry
from app.schemas.entry import (
    EntryCreateRequest,
    EntryListParams,
    EntryListResponse,
    EntryResponse,
    EntryUpdateRequest,
)
from app.services.tag_service import get_tags_by_ids

logger = logging.getLogger(__name__)


async def create_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: EntryCreateRequest,
) -> EntryResponse:
    """Create a new diary entry. Deduplicates on client_id per user."""
    # Idempotency check: if client_id provided, check for existing
    if data.client_id is not None:
        result = await db.execute(
            select(Entry).where(
                Entry.user_id == user_id,
                Entry.client_id == data.client_id,
                Entry.deleted_at.is_(None),
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return EntryResponse.model_validate(existing)

    entry = Entry(
        user_id=user_id,
        title=data.title,
        body=data.body,
        mood=data.mood,
        is_favorite=data.is_favorite,
        client_id=data.client_id,
    )
    # Assign tags if provided
    if data.tag_ids:
        tags = await get_tags_by_ids(db, user_id, data.tag_ids)
        entry.tags = tags
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    logger.info("Entry created: %s by user %s", entry.id, user_id)
    return EntryResponse.model_validate(entry)


async def list_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    params: EntryListParams,
) -> EntryListResponse:
    """List diary entries with pagination and filtering."""
    base_filter = [Entry.user_id == user_id, Entry.deleted_at.is_(None)]

    if params.mood is not None:
        base_filter.append(Entry.mood == params.mood)
    if params.is_favorite is not None:
        base_filter.append(Entry.is_favorite == params.is_favorite)
    if params.date_from is not None:
        base_filter.append(Entry.created_at >= params.date_from)
    if params.date_to is not None:
        base_filter.append(Entry.created_at <= params.date_to)
    if params.updated_since is not None:
        base_filter.append(Entry.updated_at > params.updated_since)

    # Count total
    count_query = select(func.count()).select_from(Entry).where(*base_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch page
    offset = (params.page - 1) * params.page_size
    query = (
        select(Entry)
        .where(*base_filter)
        .order_by(Entry.created_at.desc())
        .offset(offset)
        .limit(params.page_size)
    )
    result = await db.execute(query)
    entries = result.scalars().all()

    return EntryListResponse(
        entries=[EntryResponse.model_validate(e) for e in entries],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


async def get_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_id: uuid.UUID,
) -> EntryResponse:
    """Get a single entry by ID. Raises NotFoundError if missing or deleted."""
    entry = await _get_user_entry(db, user_id, entry_id)
    return EntryResponse.model_validate(entry)


async def update_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_id: uuid.UUID,
    data: EntryUpdateRequest,
) -> EntryResponse:
    """Update an entry with optimistic concurrency check."""
    entry = await _get_user_entry(db, user_id, entry_id)

    # Optimistic concurrency
    if entry.version != data.expected_version:
        raise ConflictError(
            f"Version conflict: expected {data.expected_version}, current is {entry.version}."
        )

    if data.title is not None:
        entry.title = data.title
    if data.body is not None:
        entry.body = data.body
    if data.mood is not None:
        entry.mood = data.mood
    if data.is_favorite is not None:
        entry.is_favorite = data.is_favorite

    # Update tags if provided
    if data.tag_ids is not None:
        tags = await get_tags_by_ids(db, user_id, data.tag_ids)
        entry.tags = tags

    entry.version += 1
    await db.flush()
    await db.refresh(entry)
    logger.info("Entry updated: %s (v%d)", entry.id, entry.version)
    return EntryResponse.model_validate(entry)


async def delete_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_id: uuid.UUID,
) -> None:
    """Soft-delete an entry by setting deleted_at."""
    entry = await _get_user_entry(db, user_id, entry_id)
    entry.deleted_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(entry)
    logger.info("Entry soft-deleted: %s", entry.id)


async def search_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    page: int = 1,
    page_size: int = 20,
) -> EntryListResponse:
    """Search entries by title/body text (case-insensitive LIKE for portability)."""
    pattern = f"%{query}%"
    base_filter = [
        Entry.user_id == user_id,
        Entry.deleted_at.is_(None),
        (Entry.title.ilike(pattern)) | (Entry.body.ilike(pattern)),
    ]

    # Count
    count_query = select(func.count()).select_from(Entry).where(*base_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch page
    offset = (page - 1) * page_size
    fetch_query = (
        select(Entry)
        .where(*base_filter)
        .order_by(Entry.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(fetch_query)
    entries = result.scalars().all()

    return EntryListResponse(
        entries=[EntryResponse.model_validate(e) for e in entries],
        page=page,
        page_size=page_size,
        total=total,
    )


async def _get_user_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_id: uuid.UUID,
) -> Entry:
    """Fetch entry, ensuring it belongs to the user and is not deleted."""
    result = await db.execute(
        select(Entry).where(
            Entry.id == entry_id,
            Entry.deleted_at.is_(None),
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundError("Entry")
    if entry.user_id != user_id:
        raise ForbiddenError("You do not own this entry.")
    return entry
