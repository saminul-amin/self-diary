"""Unit tests for attachment service business logic."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.services.attachment_service import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    _sanitize_filename,
    _validate_file,
    delete_attachment,
    list_attachments,
    upload_attachment,
)


def _make_entry(user_id, entry_id=None):
    entry = MagicMock()
    entry.id = entry_id or uuid.uuid4()
    entry.user_id = user_id
    entry.deleted_at = None
    return entry


def _make_attachment(entry_id, attachment_id=None):
    att = MagicMock()
    att.id = attachment_id or uuid.uuid4()
    att.entry_id = entry_id
    att.file_name = "photo.jpg"
    att.file_type = "image/jpeg"
    att.file_size = 1024
    att.storage_key = f"{uuid.uuid4()}/photo.jpg"
    att.created_at = MagicMock()
    return att


def _mock_scalar_one_or_none(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


class TestValidateFile:
    def test_valid_jpeg(self):
        file = MagicMock(spec=UploadFile)
        file.content_type = "image/jpeg"
        _validate_file(file, b"x" * 1000)

    def test_rejects_invalid_mime_type(self):
        file = MagicMock(spec=UploadFile)
        file.content_type = "application/zip"
        with pytest.raises(AppError, match="not allowed"):
            _validate_file(file, b"x" * 100)

    def test_rejects_oversized_file(self):
        file = MagicMock(spec=UploadFile)
        file.content_type = "image/png"
        with pytest.raises(AppError, match="exceeds the maximum"):
            _validate_file(file, b"x" * (MAX_FILE_SIZE + 1))

    def test_all_allowed_types_pass(self):
        for mime in ALLOWED_MIME_TYPES:
            file = MagicMock(spec=UploadFile)
            file.content_type = mime
            _validate_file(file, b"x" * 100)  # Should not raise


class TestSanitizeFilename:
    def test_simple_filename(self):
        assert _sanitize_filename("photo.jpg") == "photo.jpg"

    def test_strips_directory_unix(self):
        assert _sanitize_filename("/etc/passwd") == "passwd"

    def test_strips_directory_windows(self):
        assert _sanitize_filename("C:\\Users\\test\\evil.exe") == "evil.exe"

    def test_fallback_for_empty(self):
        assert _sanitize_filename("") == "unnamed"


class TestUploadAttachment:
    @pytest.mark.asyncio
    async def test_upload_validates_ownership(self):
        owner = uuid.uuid4()
        other = uuid.uuid4()
        entry = _make_entry(user_id=owner)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)

        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(return_value=b"data")
        file.content_type = "image/jpeg"
        file.filename = "photo.jpg"

        with pytest.raises(ForbiddenError):
            await upload_attachment(db, other, entry.id, file)

    @pytest.mark.asyncio
    async def test_upload_success(self):
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)
        db.refresh = AsyncMock(side_effect=lambda _: None)

        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(return_value=b"file-content")
        file.content_type = "image/png"
        file.filename = "screenshot.png"

        with patch("app.services.attachment_service.s3_client") as mock_s3:
            mock_s3.generate_storage_key.return_value = "key/path"
            mock_s3.generate_presigned_url.return_value = "https://s3/presigned"

            with patch("app.services.attachment_service.AttachmentResponse") as mock_resp_cls:
                mock_resp = MagicMock()
                mock_resp.file_name = "screenshot.png"
                mock_resp_cls.return_value = mock_resp
                result = await upload_attachment(db, user_id, entry.id, file)

        assert result.file_name == "screenshot.png"
        db.add.assert_called_once()


class TestDeleteAttachment:
    @pytest.mark.asyncio
    async def test_delete_raises_not_found(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        with pytest.raises(NotFoundError):
            await delete_attachment(db, uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_delete_verifies_ownership_via_entry(self):
        owner = uuid.uuid4()
        other = uuid.uuid4()
        entry = _make_entry(user_id=owner)
        att = _make_attachment(entry_id=entry.id)

        db = AsyncMock()
        # First call: find attachment; Second call: find entry (ownership check)
        db.execute.side_effect = [
            _mock_scalar_one_or_none(att),
            _mock_scalar_one_or_none(entry),
        ]

        with pytest.raises(ForbiddenError):
            await delete_attachment(db, other, att.id)


class TestListAttachments:
    @pytest.mark.asyncio
    async def test_list_returns_attachments_with_urls(self):
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id)
        att = _make_attachment(entry_id=entry.id)

        db = AsyncMock()
        # First call: entry ownership; Second call: list
        mock_entry_result = _mock_scalar_one_or_none(entry)
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [att]
        db.execute.side_effect = [mock_entry_result, mock_list_result]

        with patch("app.services.attachment_service.s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://s3/url"
            result = await list_attachments(db, user_id, entry.id)

        assert len(result.attachments) == 1
