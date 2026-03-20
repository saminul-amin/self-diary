"""
Integration tests — end-to-end API flows.

These test multi-step scenarios that span multiple endpoints,
verifying that the full stack works together correctly.
"""

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str = "flow@test.com"):
    """Helper: register a user and return auth headers."""
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "TestPass123!", "display_name": "Flow User"},
    )
    resp = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "TestPass123!"},
    )
    token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestEntryLifecycleFlow:
    """Full entry lifecycle: create → get → update → search → soft-delete → verify gone."""

    @pytest.mark.asyncio
    async def test_full_entry_lifecycle(self, client: AsyncClient):
        headers = await _register_and_login(client, "lifecycle@test.com")

        # 1. Create entry
        create_resp = await client.post(
            "/v1/entries",
            json={"title": "My First Day", "body": "Today was great!", "mood": "great"},
            headers=headers,
        )
        assert create_resp.status_code == 201
        entry = create_resp.json()
        entry_id = entry["id"]
        assert entry["version"] == 1

        # 2. Get entry
        get_resp = await client.get(f"/v1/entries/{entry_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "My First Day"

        # 3. Update entry
        update_resp = await client.put(
            f"/v1/entries/{entry_id}",
            json={"title": "My First Day (edited)", "expected_version": 1},
            headers=headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["version"] == 2
        assert update_resp.json()["title"] == "My First Day (edited)"

        # 4. Search finds updated entry
        search_resp = await client.get(
            "/v1/entries/search", params={"q": "edited"}, headers=headers
        )
        assert search_resp.status_code == 200
        assert search_resp.json()["total"] >= 1

        # 5. Soft-delete entry
        del_resp = await client.delete(f"/v1/entries/{entry_id}", headers=headers)
        assert del_resp.status_code == 204

        # 6. Deleted entry returns 404
        gone_resp = await client.get(f"/v1/entries/{entry_id}", headers=headers)
        assert gone_resp.status_code == 404


class TestTagEntryIntegrationFlow:
    """Tags + entries: create tags → create entry with tags → verify → remove tag."""

    @pytest.mark.asyncio
    async def test_tag_entry_workflow(self, client: AsyncClient):
        headers = await _register_and_login(client, "tagflow@test.com")

        # Create two tags
        t1 = await client.post(
            "/v1/tags", json={"name": "work", "color": "#FF0000"}, headers=headers
        )
        t2 = await client.post(
            "/v1/tags", json={"name": "personal", "color": "#00FF00"}, headers=headers
        )
        tag1_id = t1.json()["id"]
        tag2_id = t2.json()["id"]

        # Create entry with both tags
        entry_resp = await client.post(
            "/v1/entries",
            json={"body": "Tagged entry", "tag_ids": [tag1_id, tag2_id]},
            headers=headers,
        )
        entry = entry_resp.json()
        assert len(entry["tags"]) == 2

        # Update entry to remove one tag
        update_resp = await client.put(
            f"/v1/entries/{entry['id']}",
            json={"expected_version": 1, "tag_ids": [tag1_id]},
            headers=headers,
        )
        assert len(update_resp.json()["tags"]) == 1

        # Delete tag and verify entry still works
        await client.delete(f"/v1/tags/{tag2_id}", headers=headers)
        entry_resp = await client.get(f"/v1/entries/{entry['id']}", headers=headers)
        assert entry_resp.status_code == 200


class TestAuthTokenRotationFlow:
    """Auth: register → login → refresh → logout → verify revoked."""

    @pytest.mark.asyncio
    async def test_auth_token_rotation(self, client: AsyncClient):
        # Register
        reg_resp = await client.post(
            "/v1/auth/register",
            json={"email": "rotation@test.com", "password": "Secure123!"},
        )
        assert reg_resp.status_code == 201
        tokens = reg_resp.json()["tokens"]
        access = tokens["access_token"]
        refresh = tokens["refresh_token"]

        # Use access token
        me_resp = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert me_resp.status_code == 200

        # Refresh tokens
        ref_resp = await client.post("/v1/auth/refresh", json={"refresh_token": refresh})
        assert ref_resp.status_code == 200
        new_tokens = ref_resp.json()
        new_access = new_tokens["access_token"]
        new_refresh = new_tokens["refresh_token"]

        # Old refresh token is revoked
        old_ref_resp = await client.post("/v1/auth/refresh", json={"refresh_token": refresh})
        assert old_ref_resp.status_code == 401

        # New tokens work
        me_resp2 = await client.get(
            "/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"}
        )
        assert me_resp2.status_code == 200

        # Logout
        await client.post(
            "/v1/auth/logout",
            json={"refresh_token": new_refresh},
            headers={"Authorization": f"Bearer {new_access}"},
        )

        # Refreshing after logout fails
        post_logout = await client.post("/v1/auth/refresh", json={"refresh_token": new_refresh})
        assert post_logout.status_code == 401


class TestIdempotentCreateFlow:
    """Idempotent create: same client_id returns same entry."""

    @pytest.mark.asyncio
    async def test_idempotent_create(self, client: AsyncClient):
        headers = await _register_and_login(client, "idempotent@test.com")

        import uuid

        client_id = str(uuid.uuid4())

        # First create
        r1 = await client.post(
            "/v1/entries",
            json={"body": "Offline entry", "client_id": client_id},
            headers=headers,
        )
        assert r1.status_code == 201
        entry1 = r1.json()

        # Second create with same client_id — should return same entry
        r2 = await client.post(
            "/v1/entries",
            json={"body": "Offline entry duplicate", "client_id": client_id},
            headers=headers,
        )
        assert r2.status_code == 201
        entry2 = r2.json()

        assert entry1["id"] == entry2["id"]
        assert entry2["body"] == "Offline entry"  # original, not the duplicate


class TestOptimisticConcurrencyFlow:
    """Version conflicts: two updates with same version → 409."""

    @pytest.mark.asyncio
    async def test_version_conflict(self, client: AsyncClient):
        headers = await _register_and_login(client, "conflict@test.com")

        # Create entry
        create_resp = await client.post(
            "/v1/entries",
            json={"body": "Concurrent test"},
            headers=headers,
        )
        entry = create_resp.json()

        # First update (v1 → v2) succeeds
        r1 = await client.put(
            f"/v1/entries/{entry['id']}",
            json={"title": "Update A", "expected_version": 1},
            headers=headers,
        )
        assert r1.status_code == 200
        assert r1.json()["version"] == 2

        # Second update with stale version (v1) → 409
        r2 = await client.put(
            f"/v1/entries/{entry['id']}",
            json={"title": "Update B", "expected_version": 1},
            headers=headers,
        )
        assert r2.status_code == 409


class TestPaginationFlow:
    """Pagination: create many entries, verify page navigation."""

    @pytest.mark.asyncio
    async def test_pagination_and_filtering(self, client: AsyncClient):
        headers = await _register_and_login(client, "pagination@test.com")

        # Create 5 entries with different moods
        moods = ["great", "good", "neutral", "bad", "terrible"]
        for i, mood in enumerate(moods):
            await client.post(
                "/v1/entries",
                json={"title": f"Entry {i}", "body": f"Content {i}", "mood": mood},
                headers=headers,
            )

        # List all — should return 5
        all_resp = await client.get("/v1/entries", params={"page_size": 10}, headers=headers)
        assert all_resp.json()["total"] == 5

        # Paginate with page_size=2
        p1 = await client.get("/v1/entries", params={"page_size": 2, "page": 1}, headers=headers)
        assert len(p1.json()["entries"]) == 2

        p3 = await client.get("/v1/entries", params={"page_size": 2, "page": 3}, headers=headers)
        assert len(p3.json()["entries"]) == 1

        # Filter by mood
        mood_resp = await client.get("/v1/entries", params={"mood": "great"}, headers=headers)
        assert mood_resp.json()["total"] == 1


class TestCrossUserIsolationFlow:
    """Security: users cannot access each other's data."""

    @pytest.mark.asyncio
    async def test_cross_user_isolation(self, client: AsyncClient):
        headers_a = await _register_and_login(client, "alice@test.com")
        headers_b = await _register_and_login(client, "bob@test.com")

        # Alice creates an entry
        alice_entry = await client.post(
            "/v1/entries",
            json={"body": "Alice's private entry"},
            headers=headers_a,
        )
        entry_id = alice_entry.json()["id"]

        # Bob cannot read Alice's entry
        bob_get = await client.get(f"/v1/entries/{entry_id}", headers=headers_b)
        assert bob_get.status_code == 403

        # Bob cannot update Alice's entry
        bob_update = await client.put(
            f"/v1/entries/{entry_id}",
            json={"title": "Hacked", "expected_version": 1},
            headers=headers_b,
        )
        assert bob_update.status_code == 403

        # Bob cannot delete Alice's entry
        bob_delete = await client.delete(f"/v1/entries/{entry_id}", headers=headers_b)
        assert bob_delete.status_code == 403

        # Alice creates a tag
        alice_tag = await client.post("/v1/tags", json={"name": "secret"}, headers=headers_a)
        tag_id = alice_tag.json()["id"]

        # Bob cannot delete Alice's tag
        bob_del_tag = await client.delete(f"/v1/tags/{tag_id}", headers=headers_b)
        assert bob_del_tag.status_code == 403
