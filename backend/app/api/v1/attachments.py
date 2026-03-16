"""
Attachment API endpoints.

POST   /entries/{entry_id}/attachments  — Upload attachment (multipart)
GET    /entries/{entry_id}/attachments  — List attachments with download URLs
DELETE /attachments/{attachment_id}     — Delete attachment
"""

import uuid

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.attachment import AttachmentListResponse, AttachmentResponse
from app.services import attachment_service

router = APIRouter()


@router.post(
    "/entries/{entry_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    entry_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttachmentResponse:
    return await attachment_service.upload_attachment(
        db, user_id=current_user.id, entry_id=entry_id, file=file
    )


@router.get(
    "/entries/{entry_id}/attachments",
    response_model=AttachmentListResponse,
)
async def list_attachments(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttachmentListResponse:
    return await attachment_service.list_attachments(db, user_id=current_user.id, entry_id=entry_id)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await attachment_service.delete_attachment(
        db, user_id=current_user.id, attachment_id=attachment_id
    )
