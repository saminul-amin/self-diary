"""
Tag API endpoints.

GET    /tags          — List user's tags with entry counts
POST   /tags          — Create a new tag
PUT    /tags/{id}     — Update a tag
DELETE /tags/{id}     — Delete a tag
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.tag import (
    TagCreateRequest,
    TagListResponse,
    TagResponse,
    TagUpdateRequest,
)
from app.services import tag_service

router = APIRouter()


@router.get("", response_model=TagListResponse)
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagListResponse:
    return await tag_service.list_tags(db, user_id=current_user.id)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    body: TagCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    return await tag_service.create_tag(db, user_id=current_user.id, data=body)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    body: TagUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    return await tag_service.update_tag(db, user_id=current_user.id, tag_id=tag_id, data=body)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await tag_service.delete_tag(db, user_id=current_user.id, tag_id=tag_id)
