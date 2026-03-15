"""
Integration tests for diary entry endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

TEST_USER = {
    "email": "entry_user@example.com",
    "password": "securepassword123",
    "display_name": "Entry Tester",
}


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a test user and return Authorization headers."""
    resp = await client.post("/v1/auth/register", json=TEST_USER)
    token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── CREATE ──


@pytest.mark.asyncio
async def test_create_entry(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.post(
        "/v1/entries",
        json={"title": "My Day", "body": "Today was great!", "mood": "great"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My Day"
    assert data["body"] == "Today was great!"
    assert data["mood"] == "great"
    assert data["version"] == 1
    assert data["is_favorite"] is False


@pytest.mark.asyncio
async def test_create_entry_minimal(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.post(
        "/v1/entries",
        json={"body": "Just a quick note."},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] is None
    assert data["mood"] is None


@pytest.mark.asyncio
async def test_create_entry_empty_body(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.post(
        "/v1/entries",
        json={"body": ""},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_entry_no_auth(client: AsyncClient) -> None:
    resp = await client.post("/v1/entries", json={"body": "No auth"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_entry_idempotent(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    cid = str(uuid.uuid4())
    payload = {"body": "Idempotent entry", "client_id": cid}

    resp1 = await client.post("/v1/entries", json=payload, headers=headers)
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    resp2 = await client.post("/v1/entries", json=payload, headers=headers)
    assert resp2.status_code == 201
    id2 = resp2.json()["id"]

    assert id1 == id2  # same entry returned


# ── LIST ──


@pytest.mark.asyncio
async def test_list_entries_empty(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.get("/v1/entries", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["entries"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_entries_pagination(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    # Create 5 entries
    for i in range(5):
        await client.post(
            "/v1/entries",
            json={"body": f"Entry {i}"},
            headers=headers,
        )

    # Page 1, size 2
    resp = await client.get("/v1/entries?page=1&page_size=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["entries"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1

    # Page 3, size 2 → 1 entry
    resp = await client.get("/v1/entries?page=3&page_size=2", headers=headers)
    data = resp.json()
    assert len(data["entries"]) == 1


@pytest.mark.asyncio
async def test_list_entries_filter_mood(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    await client.post("/v1/entries", json={"body": "Good day", "mood": "good"}, headers=headers)
    await client.post("/v1/entries", json={"body": "Bad day", "mood": "bad"}, headers=headers)

    resp = await client.get("/v1/entries?mood=good", headers=headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["entries"][0]["mood"] == "good"


@pytest.mark.asyncio
async def test_list_entries_filter_favorite(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    await client.post("/v1/entries", json={"body": "Fav", "is_favorite": True}, headers=headers)
    await client.post(
        "/v1/entries", json={"body": "Not fav", "is_favorite": False}, headers=headers
    )

    resp = await client.get("/v1/entries?is_favorite=true", headers=headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["entries"][0]["is_favorite"] is True


# ── GET SINGLE ──


@pytest.mark.asyncio
async def test_get_entry(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_resp = await client.post("/v1/entries", json={"body": "Detail test"}, headers=headers)
    entry_id = create_resp.json()["id"]

    resp = await client.get(f"/v1/entries/{entry_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == entry_id


@pytest.mark.asyncio
async def test_get_entry_not_found(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/v1/entries/{fake_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_entry_other_user(client: AsyncClient) -> None:
    """User A cannot access User B's entry."""
    # User A
    resp_a = await client.post("/v1/auth/register", json=TEST_USER)
    headers_a = {"Authorization": f"Bearer {resp_a.json()['tokens']['access_token']}"}

    create_resp = await client.post("/v1/entries", json={"body": "Private"}, headers=headers_a)
    entry_id = create_resp.json()["id"]

    # User B
    resp_b = await client.post(
        "/v1/auth/register",
        json={"email": "other@example.com", "password": "securepassword123"},
    )
    headers_b = {"Authorization": f"Bearer {resp_b.json()['tokens']['access_token']}"}

    resp = await client.get(f"/v1/entries/{entry_id}", headers=headers_b)
    assert resp.status_code == 403


# ── UPDATE ──


@pytest.mark.asyncio
async def test_update_entry(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_resp = await client.post("/v1/entries", json={"body": "Original"}, headers=headers)
    entry_id = create_resp.json()["id"]

    resp = await client.put(
        f"/v1/entries/{entry_id}",
        json={"body": "Updated body", "expected_version": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["body"] == "Updated body"
    assert data["version"] == 2


@pytest.mark.asyncio
async def test_update_entry_version_conflict(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_resp = await client.post("/v1/entries", json={"body": "Original"}, headers=headers)
    entry_id = create_resp.json()["id"]

    # First update succeeds (v1 → v2)
    await client.put(
        f"/v1/entries/{entry_id}",
        json={"body": "V2", "expected_version": 1},
        headers=headers,
    )

    # Second update with stale version (expects v1, but now v2)
    resp = await client.put(
        f"/v1/entries/{entry_id}",
        json={"body": "Stale", "expected_version": 1},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_update_entry_not_found(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    fake_id = str(uuid.uuid4())
    resp = await client.put(
        f"/v1/entries/{fake_id}",
        json={"body": "Nope", "expected_version": 1},
        headers=headers,
    )
    assert resp.status_code == 404


# ── DELETE ──


@pytest.mark.asyncio
async def test_delete_entry(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_resp = await client.post("/v1/entries", json={"body": "To delete"}, headers=headers)
    entry_id = create_resp.json()["id"]

    resp = await client.delete(f"/v1/entries/{entry_id}", headers=headers)
    assert resp.status_code == 204

    # Should not appear in list
    list_resp = await client.get("/v1/entries", headers=headers)
    ids = [e["id"] for e in list_resp.json()["entries"]]
    assert entry_id not in ids

    # Should return 404 on direct fetch
    get_resp = await client.get(f"/v1/entries/{entry_id}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_entry_not_found(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    fake_id = str(uuid.uuid4())
    resp = await client.delete(f"/v1/entries/{fake_id}", headers=headers)
    assert resp.status_code == 404


# ── SEARCH ──


@pytest.mark.asyncio
async def test_search_entries(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    await client.post(
        "/v1/entries", json={"title": "Beach Holiday", "body": "Went swimming."}, headers=headers
    )
    await client.post(
        "/v1/entries", json={"title": "Work Day", "body": "Meetings all day."}, headers=headers
    )

    resp = await client.get("/v1/entries/search?q=swimming", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "swimming" in data["entries"][0]["body"].lower()


@pytest.mark.asyncio
async def test_search_entries_no_results(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.get("/v1/entries/search?q=nonexistent", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_entries_missing_query(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    resp = await client.get("/v1/entries/search", headers=headers)
    assert resp.status_code == 422
