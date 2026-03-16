"""
Tag service — business logic for tag CRUD and entry-tag linking.
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.tag import Tag, entry_tags
from app.schemas.tag import (
    TagCreateRequest,
    TagListResponse,
    TagResponse,
    TagUpdateRequest,
    TagWithCountResponse,
)

logger = logging.getLogger(__name__)


async def list_tags(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> TagListResponse:
    """List all tags for a user with entry counts."""
    query = (
        select(Tag, func.count(entry_tags.c.entry_id).label("entry_count"))
        .outerjoin(entry_tags, Tag.id == entry_tags.c.tag_id)
        .where(Tag.user_id == user_id)
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    result = await db.execute(query)
    rows = result.all()

    tags = [
        TagWithCountResponse(
            id=tag.id,
            user_id=tag.user_id,
            name=tag.name,
            color=tag.color,
            created_at=tag.created_at,
            entry_count=count,
        )
        for tag, count in rows
    ]
    return TagListResponse(tags=tags)


async def create_tag(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: TagCreateRequest,
) -> TagResponse:
    """Create a new tag for a user. Raises ConflictError on duplicate name."""
    existing = await db.execute(select(Tag).where(Tag.user_id == user_id, Tag.name == data.name))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Tag '{data.name}' already exists.")

    tag = Tag(user_id=user_id, name=data.name, color=data.color)
    db.add(tag)
    await db.flush()
    logger.info("Tag created: %s by user %s", tag.id, user_id)
    return TagResponse.model_validate(tag)


async def update_tag(
    db: AsyncSession,
    user_id: uuid.UUID,
    tag_id: uuid.UUID,
    data: TagUpdateRequest,
) -> TagResponse:
    """Update tag name and/or color."""
    tag = await _get_user_tag(db, user_id, tag_id)

    if data.name is not None:
        # Check for duplicate name
        existing = await db.execute(
            select(Tag).where(Tag.user_id == user_id, Tag.name == data.name, Tag.id != tag_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(f"Tag '{data.name}' already exists.")
        tag.name = data.name

    if data.color is not None:
        tag.color = data.color

    await db.flush()
    logger.info("Tag updated: %s", tag.id)
    return TagResponse.model_validate(tag)


async def delete_tag(
    db: AsyncSession,
    user_id: uuid.UUID,
    tag_id: uuid.UUID,
) -> None:
    """Delete a tag and all its entry associations (cascade)."""
    tag = await _get_user_tag(db, user_id, tag_id)

    # Clear the relationship first so SQLAlchemy doesn't double-delete
    tag.entries = []
    await db.flush()
    await db.delete(tag)
    await db.flush()
    logger.info("Tag deleted: %s", tag_id)


async def get_tags_by_ids(
    db: AsyncSession,
    user_id: uuid.UUID,
    tag_ids: list[uuid.UUID],
) -> list[Tag]:
    """Fetch multiple tags by IDs, ensuring they belong to the user."""
    if not tag_ids:
        return []
    result = await db.execute(select(Tag).where(Tag.user_id == user_id, Tag.id.in_(tag_ids)))
    tags = list(result.scalars().all())
    if len(tags) != len(set(tag_ids)):
        found = {t.id for t in tags}
        missing = set(tag_ids) - found
        raise NotFoundError(f"Tags not found: {missing}")
    return tags


async def _get_user_tag(
    db: AsyncSession,
    user_id: uuid.UUID,
    tag_id: uuid.UUID,
) -> Tag:
    """Fetch a tag, ensuring it belongs to the user."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if tag is None:
        raise NotFoundError("Tag")
    if tag.user_id != user_id:
        raise ForbiddenError("You do not own this tag.")
    return tag
