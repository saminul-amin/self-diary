"""Unit tests for tag service business logic."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.schemas.tag import TagCreateRequest, TagUpdateRequest
from app.services.tag_service import (
    create_tag,
    delete_tag,
    get_tags_by_ids,
    list_tags,
    update_tag,
)


def _make_tag(user_id=None, tag_id=None, name="work", color="#FF0000"):
    tag = MagicMock()
    tag.id = tag_id or uuid.uuid4()
    tag.user_id = user_id or uuid.uuid4()
    tag.name = name
    tag.color = color
    tag.created_at = datetime.now(UTC)
    tag.entries = []
    return tag


def _mock_scalar_one_or_none(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


class TestCreateTag:
    @pytest.mark.asyncio
    async def test_create_raises_conflict_on_duplicate_name(self):
        user_id = uuid.uuid4()
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(_make_tag(user_id=user_id))

        data = TagCreateRequest(name="work")
        with pytest.raises(ConflictError, match="already exists"):
            await create_tag(db, user_id, data)

    @pytest.mark.asyncio
    async def test_create_tag_success(self):
        user_id = uuid.uuid4()
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        data = TagCreateRequest(name="travel", color="#00FF00")
        with patch("app.services.tag_service.TagResponse") as mock_resp_cls:
            mock_resp_cls.model_validate.return_value = MagicMock()
            await create_tag(db, user_id, data)

        db.add.assert_called_once()
        db.flush.assert_called_once()


class TestUpdateTag:
    @pytest.mark.asyncio
    async def test_update_raises_not_found(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        data = TagUpdateRequest(name="new-name")
        with pytest.raises(NotFoundError):
            await update_tag(db, uuid.uuid4(), uuid.uuid4(), data)

    @pytest.mark.asyncio
    async def test_update_raises_forbidden_for_other_user(self):
        owner = uuid.uuid4()
        other = uuid.uuid4()
        tag = _make_tag(user_id=owner)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(tag)

        data = TagUpdateRequest(name="new-name")
        with pytest.raises(ForbiddenError):
            await update_tag(db, other, tag.id, data)

    @pytest.mark.asyncio
    async def test_update_name_checks_duplicate(self):
        user_id = uuid.uuid4()
        tag = _make_tag(user_id=user_id, name="work")
        existing_dup = _make_tag(user_id=user_id, name="personal")
        db = AsyncMock()
        # First call: find tag → found; Second call: check duplicate name → found
        db.execute.side_effect = [
            _mock_scalar_one_or_none(tag),
            _mock_scalar_one_or_none(existing_dup),
        ]

        data = TagUpdateRequest(name="personal")
        with pytest.raises(ConflictError, match="already exists"):
            await update_tag(db, user_id, tag.id, data)

    @pytest.mark.asyncio
    async def test_update_color_only(self):
        user_id = uuid.uuid4()
        tag = _make_tag(user_id=user_id, color="#000000")
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(tag)

        data = TagUpdateRequest(color="#FFFFFF")
        await update_tag(db, user_id, tag.id, data)

        assert tag.color == "#FFFFFF"


class TestDeleteTag:
    @pytest.mark.asyncio
    async def test_delete_clears_associations_and_deletes(self):
        user_id = uuid.uuid4()
        tag = _make_tag(user_id=user_id)
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(tag)

        await delete_tag(db, user_id, tag.id)

        assert tag.entries == []
        db.delete.assert_called_once_with(tag)
        assert db.flush.call_count == 2  # clear associations + delete

    @pytest.mark.asyncio
    async def test_delete_raises_not_found(self):
        db = AsyncMock()
        db.execute.return_value = _mock_scalar_one_or_none(None)

        with pytest.raises(NotFoundError):
            await delete_tag(db, uuid.uuid4(), uuid.uuid4())


class TestGetTagsByIds:
    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_ids(self):
        db = AsyncMock()
        result = await get_tags_by_ids(db, uuid.uuid4(), [])
        assert result == []
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_tag_not_found(self):
        user_id = uuid.uuid4()
        tag_id1 = uuid.uuid4()
        tag_id2 = uuid.uuid4()

        tag1 = _make_tag(user_id=user_id, tag_id=tag_id1)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [tag1]
        db.execute.return_value = mock_result

        with pytest.raises(NotFoundError, match="Tags not found"):
            await get_tags_by_ids(db, user_id, [tag_id1, tag_id2])


class TestListTags:
    @pytest.mark.asyncio
    async def test_list_returns_tags_with_counts(self):
        user_id = uuid.uuid4()
        tag = _make_tag(user_id=user_id, name="work")
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(tag, 5)]
        db.execute.return_value = mock_result

        result = await list_tags(db, user_id)

        assert len(result.tags) == 1
        assert result.tags[0].name == "work"
        assert result.tags[0].entry_count == 5
