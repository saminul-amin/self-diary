"""Unit tests for entry service business logic."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.schemas.entry import EntryCreateRequest, EntryListParams, EntryUpdateRequest
from app.services.entry_service import (
    create_entry,
    delete_entry,
    get_entry,
    list_entries,
    search_entries,
    update_entry,
)


def _make_entry(user_id=None, entry_id=None, version=1, title="Test", body="Body text"):
    """Create a mock Entry object."""
    entry = MagicMock()
    entry.id = entry_id or uuid.uuid4()
    entry.user_id = user_id or uuid.uuid4()
    entry.title = title
    entry.body = body
    entry.mood = None
    entry.is_favorite = False
    entry.version = version
    entry.client_id = None
    entry.created_at = datetime.now(UTC)
    entry.updated_at = datetime.now(UTC)
    entry.deleted_at = None
    entry.tags = []
    return entry


def _mock_scalar_one_or_none(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _mock_scalar_one(value):
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


class TestCreateEntry:
    @pytest.mark.asyncio
    async def test_create_entry_with_client_id_deduplicates(self):
        """If client_id already exists, return existing entry instead of creating."""
        user_id = uuid.uuid4()
        existing = _make_entry(user_id=user_id)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(existing)

        data = EntryCreateRequest(body="test", client_id=uuid.uuid4())
        result = await create_entry(db, user_id, data)

        assert result.id == existing.id
        db.add.assert_not_called()  # Should not add a new entry

    @pytest.mark.asyncio
    async def test_create_entry_without_client_id(self):
        """New entry created when no client_id is provided."""
        user_id = uuid.uuid4()
        db = AsyncMock()
        # refresh returns the entry so model_validate works
        db.refresh = AsyncMock(side_effect=lambda _: None)

        data = EntryCreateRequest(body="My diary entry")

        with patch("app.services.entry_service.EntryResponse") as mock_resp_cls:
            mock_resp_cls.model_validate.return_value = MagicMock()
            await create_entry(db, user_id, data)

        db.add.assert_called_once()
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_entry_with_tags(self):
        """Tags are resolved and assigned to the entry."""
        user_id = uuid.uuid4()
        tag_id = uuid.uuid4()
        mock_tag = MagicMock()
        db = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda _: None)

        data = EntryCreateRequest(body="Tagged entry", tag_ids=[tag_id])

        with (
            patch("app.services.entry_service.get_tags_by_ids", return_value=[mock_tag]),
            patch("app.services.entry_service.EntryResponse") as mock_resp_cls,
        ):
            mock_resp_cls.model_validate.return_value = MagicMock()
            await create_entry(db, user_id, data)

        db.add.assert_called_once()


class TestGetEntry:
    @pytest.mark.asyncio
    async def test_get_entry_returns_entry(self):
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)

        result = await get_entry(db, user_id, entry.id)
        assert result.id == entry.id

    @pytest.mark.asyncio
    async def test_get_entry_raises_not_found(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        with pytest.raises(NotFoundError):
            await get_entry(db, uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_entry_raises_forbidden_for_other_user(self):
        owner = uuid.uuid4()
        other_user = uuid.uuid4()
        entry = _make_entry(user_id=owner)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)

        with pytest.raises(ForbiddenError):
            await get_entry(db, other_user, entry.id)


class TestUpdateEntry:
    @pytest.mark.asyncio
    async def test_update_raises_version_conflict(self):
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id, version=3)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)

        data = EntryUpdateRequest(expected_version=1)  # Wrong version
        with pytest.raises(ConflictError, match="Version conflict"):
            await update_entry(db, user_id, entry.id, data)

    @pytest.mark.asyncio
    async def test_update_increments_version(self):
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id, version=2)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)

        data = EntryUpdateRequest(title="Updated", expected_version=2)
        await update_entry(db, user_id, entry.id, data)

        assert entry.version == 3
        assert entry.title == "Updated"

    @pytest.mark.asyncio
    async def test_update_with_tags(self):
        user_id = uuid.uuid4()
        tag_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id, version=1)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)
        db.refresh = AsyncMock(side_effect=lambda _: None)

        data = EntryUpdateRequest(expected_version=1, tag_ids=[tag_id])
        with (
            patch("app.services.entry_service.get_tags_by_ids", return_value=[MagicMock()]),
            patch("app.services.entry_service.EntryResponse") as mock_resp_cls,
        ):
            mock_resp_cls.model_validate.return_value = MagicMock()
            await update_entry(db, user_id, entry.id, data)

        assert entry.version == 2

    @pytest.mark.asyncio
    async def test_update_partial_fields(self):
        """Only provided fields should be updated."""
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id, version=1, title="Original", body="Original body")
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)

        data = EntryUpdateRequest(expected_version=1, body="New body")
        await update_entry(db, user_id, entry.id, data)

        assert entry.title == "Original"  # Not changed
        assert entry.body == "New body"


class TestDeleteEntry:
    @pytest.mark.asyncio
    async def test_soft_deletes_entry(self):
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(entry)

        await delete_entry(db, user_id, entry.id)
        assert entry.deleted_at is not None

    @pytest.mark.asyncio
    async def test_delete_raises_not_found(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        with pytest.raises(NotFoundError):
            await delete_entry(db, uuid.uuid4(), uuid.uuid4())


class TestListEntries:
    @pytest.mark.asyncio
    async def test_list_returns_paginated_entries(self):
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id)
        db = AsyncMock()

        # First call: count query → 1
        # Second call: fetch query → [entry]
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1
        mock_fetch_result = MagicMock()
        mock_fetch_result.scalars.return_value.all.return_value = [entry]
        db.execute.side_effect = [mock_count_result, mock_fetch_result]

        params = EntryListParams(page=1, page_size=20)
        result = await list_entries(db, user_id, params)

        assert result.total == 1
        assert result.page == 1
        assert len(result.entries) == 1

    @pytest.mark.asyncio
    async def test_list_with_mood_filter(self):
        user_id = uuid.uuid4()
        db = AsyncMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        mock_fetch_result = MagicMock()
        mock_fetch_result.scalars.return_value.all.return_value = []
        db.execute.side_effect = [mock_count_result, mock_fetch_result]

        params = EntryListParams(mood="great")
        result = await list_entries(db, user_id, params)

        assert result.total == 0
        assert result.entries == []


class TestSearchEntries:
    @pytest.mark.asyncio
    async def test_search_by_text(self):
        user_id = uuid.uuid4()
        entry = _make_entry(user_id=user_id, title="Vacation diary")
        db = AsyncMock()

        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 1
        mock_fetch = MagicMock()
        mock_fetch.scalars.return_value.all.return_value = [entry]
        db.execute.side_effect = [mock_count, mock_fetch]

        result = await search_entries(db, user_id, "vacation")

        assert result.total == 1
        assert len(result.entries) == 1
