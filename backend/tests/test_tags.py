"""
Integration tests for tag endpoints and entry-tag linking.
"""

import uuid

import pytest
from httpx import AsyncClient

TEST_USER = {
    "email": "tag_user@example.com",
    "password": "securepassword123",
    "display_name": "Tag Tester",
}


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a test user and return Authorization headers."""
    resp = await client.post("/v1/auth/register", json=TEST_USER)
    token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── TAG CRUD ──


@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.post(
        "/v1/tags",
        json={"name": "personal", "color": "#FF5733"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "personal"
    assert data["color"] == "#FF5733"


@pytest.mark.asyncio
async def test_create_tag_no_color(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.post(
        "/v1/tags",
        json={"name": "work"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["color"] is None


@pytest.mark.asyncio
async def test_create_tag_duplicate_name(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    await client.post("/v1/tags", json={"name": "dup"}, headers=headers)
    resp = await client.post("/v1/tags", json={"name": "dup"}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_tag_invalid_color(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.post(
        "/v1/tags",
        json={"name": "bad", "color": "red"},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_tag_no_auth(client: AsyncClient) -> None:
    resp = await client.post("/v1/tags", json={"name": "fail"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_tags_empty(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.get("/v1/tags", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["tags"] == []


@pytest.mark.asyncio
async def test_list_tags_with_counts(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    # Create two tags
    tag1 = await client.post("/v1/tags", json={"name": "work"}, headers=headers)
    tag2 = await client.post("/v1/tags", json={"name": "personal"}, headers=headers)
    tag1_id = tag1.json()["id"]
    tag2_id = tag2.json()["id"]

    # Create an entry with tag1
    await client.post(
        "/v1/entries",
        json={"body": "Work stuff", "tag_ids": [tag1_id]},
        headers=headers,
    )
    # Create an entry with both tags
    await client.post(
        "/v1/entries",
        json={"body": "Mixed", "tag_ids": [tag1_id, tag2_id]},
        headers=headers,
    )

    resp = await client.get("/v1/tags", headers=headers)
    data = resp.json()
    assert len(data["tags"]) == 2

    # Tags sorted by name: personal, work
    tag_map = {t["name"]: t for t in data["tags"]}
    assert tag_map["work"]["entry_count"] == 2
    assert tag_map["personal"]["entry_count"] == 1


@pytest.mark.asyncio
async def test_update_tag(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_resp = await client.post("/v1/tags", json={"name": "old"}, headers=headers)
    tag_id = create_resp.json()["id"]

    resp = await client.put(
        f"/v1/tags/{tag_id}",
        json={"name": "new", "color": "#00FF00"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "new"
    assert data["color"] == "#00FF00"


@pytest.mark.asyncio
async def test_update_tag_duplicate_name(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    await client.post("/v1/tags", json={"name": "first"}, headers=headers)
    second = await client.post("/v1/tags", json={"name": "second"}, headers=headers)
    tag_id = second.json()["id"]

    resp = await client.put(
        f"/v1/tags/{tag_id}",
        json={"name": "first"},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_tag_not_found(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    fake_id = str(uuid.uuid4())
    resp = await client.put(
        f"/v1/tags/{fake_id}",
        json={"name": "nope"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_resp = await client.post("/v1/tags", json={"name": "bye"}, headers=headers)
    tag_id = create_resp.json()["id"]

    resp = await client.delete(f"/v1/tags/{tag_id}", headers=headers)
    assert resp.status_code == 204

    # Verify it's gone
    list_resp = await client.get("/v1/tags", headers=headers)
    ids = [t["id"] for t in list_resp.json()["tags"]]
    assert tag_id not in ids


@pytest.mark.asyncio
async def test_delete_tag_not_found(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    fake_id = str(uuid.uuid4())
    resp = await client.delete(f"/v1/tags/{fake_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_tag_removes_entry_association(client: AsyncClient) -> None:
    """Deleting a tag should remove it from associated entries."""
    headers = await _auth_headers(client)
    tag_resp = await client.post("/v1/tags", json={"name": "temp"}, headers=headers)
    tag_id = tag_resp.json()["id"]

    entry_resp = await client.post(
        "/v1/entries",
        json={"body": "Tagged entry", "tag_ids": [tag_id]},
        headers=headers,
    )
    entry_id = entry_resp.json()["id"]

    # Delete the tag
    await client.delete(f"/v1/tags/{tag_id}", headers=headers)

    # Entry should still exist but have no tags
    get_resp = await client.get(f"/v1/entries/{entry_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["tags"] == []


# ── ENTRY-TAG INTEGRATION ──


@pytest.mark.asyncio
async def test_create_entry_with_tags(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    tag1 = await client.post("/v1/tags", json={"name": "diary"}, headers=headers)
    tag2 = await client.post("/v1/tags", json={"name": "happy"}, headers=headers)
    tag1_id = tag1.json()["id"]
    tag2_id = tag2.json()["id"]

    resp = await client.post(
        "/v1/entries",
        json={"body": "A happy diary entry", "tag_ids": [tag1_id, tag2_id]},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    tag_names = {t["name"] for t in data["tags"]}
    assert tag_names == {"diary", "happy"}


@pytest.mark.asyncio
async def test_create_entry_with_invalid_tag(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    fake_tag_id = str(uuid.uuid4())
    resp = await client.post(
        "/v1/entries",
        json={"body": "Bad tag ref", "tag_ids": [fake_tag_id]},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_entry_tags(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    tag1 = await client.post("/v1/tags", json={"name": "work"}, headers=headers)
    tag2 = await client.post("/v1/tags", json={"name": "fun"}, headers=headers)
    tag1_id = tag1.json()["id"]
    tag2_id = tag2.json()["id"]

    # Create entry with tag1
    entry_resp = await client.post(
        "/v1/entries",
        json={"body": "Work entry", "tag_ids": [tag1_id]},
        headers=headers,
    )
    entry_id = entry_resp.json()["id"]

    # Update to use tag2 only
    resp = await client.put(
        f"/v1/entries/{entry_id}",
        json={"expected_version": 1, "tag_ids": [tag2_id]},
        headers=headers,
    )
    assert resp.status_code == 200
    tag_names = {t["name"] for t in resp.json()["tags"]}
    assert tag_names == {"fun"}


@pytest.mark.asyncio
async def test_update_entry_clear_tags(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    tag = await client.post("/v1/tags", json={"name": "remove_me"}, headers=headers)
    tag_id = tag.json()["id"]

    entry_resp = await client.post(
        "/v1/entries",
        json={"body": "Will clear tags", "tag_ids": [tag_id]},
        headers=headers,
    )
    entry_id = entry_resp.json()["id"]

    # Clear tags by passing empty list
    resp = await client.put(
        f"/v1/entries/{entry_id}",
        json={"expected_version": 1, "tag_ids": []},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["tags"] == []


@pytest.mark.asyncio
async def test_entry_tags_in_list(client: AsyncClient) -> None:
    """Tags should appear in entry list responses."""
    headers = await _auth_headers(client)
    tag = await client.post("/v1/tags", json={"name": "listed"}, headers=headers)
    tag_id = tag.json()["id"]

    await client.post(
        "/v1/entries",
        json={"body": "Tagged in list", "tag_ids": [tag_id]},
        headers=headers,
    )

    resp = await client.get("/v1/entries", headers=headers)
    entries = resp.json()["entries"]
    assert len(entries) == 1
    assert len(entries[0]["tags"]) == 1
    assert entries[0]["tags"][0]["name"] == "listed"


@pytest.mark.asyncio
async def test_other_user_tag_isolation(client: AsyncClient) -> None:
    """User A's tags should not be visible to User B."""
    # User A
    resp_a = await client.post("/v1/auth/register", json=TEST_USER)
    headers_a = {"Authorization": f"Bearer {resp_a.json()['tokens']['access_token']}"}
    await client.post("/v1/tags", json={"name": "private"}, headers=headers_a)

    # User B
    resp_b = await client.post(
        "/v1/auth/register",
        json={"email": "other_tag@example.com", "password": "securepassword123"},
    )
    headers_b = {"Authorization": f"Bearer {resp_b.json()['tokens']['access_token']}"}

    resp = await client.get("/v1/tags", headers=headers_b)
    assert resp.json()["tags"] == []
