"""
Attachment service — business logic for file uploads, listing, and deletion.
"""

import logging
import uuid
from pathlib import PureWindowsPath

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models.attachment import Attachment
from app.models.entry import Entry
from app.schemas.attachment import AttachmentListResponse, AttachmentResponse
from app.services import s3_client

logger = logging.getLogger(__name__)

# File validation constants
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _validate_file(file: UploadFile, file_data: bytes) -> None:
    """Validate file type and size. Raises AppError (422) on failure."""
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES:
        allowed = ", ".join(sorted(ALLOWED_MIME_TYPES))
        raise AppError(
            status_code=422,
            code="INVALID_FILE_TYPE",
            message=f"File type '{content_type}' is not allowed. Allowed: {allowed}",
        )
    if len(file_data) > MAX_FILE_SIZE:
        raise AppError(
            status_code=422,
            code="FILE_TOO_LARGE",
            message="File size exceeds the maximum of 10 MB.",
        )


def _sanitize_filename(name: str) -> str:
    """Extract just the filename, stripping any directory path components."""
    return PureWindowsPath(name).name or "unnamed"


async def upload_attachment(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_id: uuid.UUID,
    file: UploadFile,
) -> AttachmentResponse:
    """Upload a file attachment to an entry."""
    # Validate entry ownership
    await _get_user_entry(db, user_id, entry_id)

    # Read and validate file
    file_data = await file.read()
    _validate_file(file, file_data)

    content_type = file.content_type or "application/octet-stream"
    file_name = _sanitize_filename(file.filename or "unnamed")

    # Upload to S3
    storage_key = s3_client.generate_storage_key(user_id, entry_id, file_name)
    s3_client.upload_file(storage_key, file_data, content_type)

    # Save metadata to DB
    attachment = Attachment(
        entry_id=entry_id,
        file_name=file_name,
        file_type=content_type,
        file_size=len(file_data),
        storage_key=storage_key,
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)

    logger.info("Attachment created: %s for entry %s", attachment.id, entry_id)

    download_url = s3_client.generate_presigned_url(storage_key)
    return AttachmentResponse(
        id=attachment.id,
        entry_id=attachment.entry_id,
        file_name=attachment.file_name,
        file_type=attachment.file_type,
        file_size=attachment.file_size,
        created_at=attachment.created_at,
        download_url=download_url,
    )


async def list_attachments(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_id: uuid.UUID,
) -> AttachmentListResponse:
    """List all attachments for an entry with pre-signed download URLs."""
    await _get_user_entry(db, user_id, entry_id)

    result = await db.execute(
        select(Attachment)
        .where(Attachment.entry_id == entry_id)
        .order_by(Attachment.created_at.desc())
    )
    attachments = result.scalars().all()

    items = []
    for att in attachments:
        download_url = s3_client.generate_presigned_url(att.storage_key)
        items.append(
            AttachmentResponse(
                id=att.id,
                entry_id=att.entry_id,
                file_name=att.file_name,
                file_type=att.file_type,
                file_size=att.file_size,
                created_at=att.created_at,
                download_url=download_url,
            )
        )

    return AttachmentListResponse(attachments=items)


async def delete_attachment(
    db: AsyncSession,
    user_id: uuid.UUID,
    attachment_id: uuid.UUID,
) -> None:
    """Delete an attachment from S3 and the database."""
    result = await db.execute(select(Attachment).where(Attachment.id == attachment_id))
    attachment = result.scalar_one_or_none()
    if attachment is None:
        raise NotFoundError("Attachment")

    # Verify ownership via entry
    await _get_user_entry(db, user_id, attachment.entry_id)

    # Delete from S3 then DB
    s3_client.delete_file(attachment.storage_key)
    await db.delete(attachment)
    await db.flush()
    logger.info("Attachment deleted: %s", attachment_id)


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
