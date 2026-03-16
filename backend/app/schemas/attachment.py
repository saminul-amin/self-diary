"""
Pydantic schemas for attachment endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: uuid.UUID
    entry_id: uuid.UUID
    file_name: str
    file_type: str
    file_size: int
    created_at: datetime
    download_url: str | None = None

    model_config = {"from_attributes": True}


class AttachmentListResponse(BaseModel):
    attachments: list[AttachmentResponse]
