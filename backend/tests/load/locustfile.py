"""
Locust load‑testing scenarios for SelfDiary API.

Usage
-----
    pip install locust
    locust -f backend/tests/load/locustfile.py --host http://localhost:8000

Then open http://localhost:8089, configure users/spawn‑rate, and start.

Target: 100 req/s sustained, P95 < 200 ms.
"""

from __future__ import annotations

import uuid

from locust import HttpUser, between, tag, task


class SelfDiaryUser(HttpUser):
    """Simulates a typical diary user: register ➜ login ➜ CRUD entries & tags ➜ search."""

    wait_time = between(0.5, 2)

    # ── lifecycle ──

    def on_start(self) -> None:
        """Register and login to obtain an access token."""
        self.email = f"load-{uuid.uuid4().hex[:12]}@test.local"
        self.password = "LoadTest123!"
        self.entry_ids: list[str] = []
        self.tag_ids: list[str] = []

        # Register
        resp = self.client.post(
            "/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "display_name": "Load Tester",
            },
            name="/v1/auth/register",
        )
        if resp.status_code == 201:
            data = resp.json()
            self._set_auth(data["tokens"]["access_token"], data["tokens"]["refresh_token"])
        else:
            # Fallback: login if already registered
            self._login()

    def _login(self) -> None:
        resp = self.client.post(
            "/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/v1/auth/login",
        )
        if resp.status_code == 200:
            data = resp.json()
            self._set_auth(data["tokens"]["access_token"], data["tokens"]["refresh_token"])

    def _set_auth(self, access: str, refresh: str) -> None:
        self.access_token = access
        self.refresh_token = refresh
        self.client.headers.update({"Authorization": f"Bearer {access}"})

    # ── entry tasks ──

    @task(5)
    @tag("entries")
    def create_entry(self) -> None:
        resp = self.client.post(
            "/v1/entries",
            json={
                "title": f"Load entry {uuid.uuid4().hex[:8]}",
                "body": "Locust load-test body content for performance benchmarking.",
                "mood": "good",
                "client_id": str(uuid.uuid4()),
            },
            name="/v1/entries [POST]",
        )
        if resp.status_code == 201:
            self.entry_ids.append(resp.json()["id"])

    @task(10)
    @tag("entries")
    def list_entries(self) -> None:
        self.client.get(
            "/v1/entries",
            params={"page": 1, "page_size": 20},
            name="/v1/entries [GET list]",
        )

    @task(3)
    @tag("entries")
    def get_entry(self) -> None:
        if not self.entry_ids:
            return
        eid = self.entry_ids[-1]
        self.client.get(f"/v1/entries/{eid}", name="/v1/entries/{id} [GET]")

    @task(2)
    @tag("entries")
    def update_entry(self) -> None:
        if not self.entry_ids:
            return
        eid = self.entry_ids[-1]
        self.client.put(
            f"/v1/entries/{eid}",
            json={"title": f"Updated {uuid.uuid4().hex[:6]}", "version": 1},
            name="/v1/entries/{id} [PUT]",
        )

    @task(1)
    @tag("entries")
    def delete_entry(self) -> None:
        if not self.entry_ids:
            return
        eid = self.entry_ids.pop(0)
        self.client.delete(f"/v1/entries/{eid}", name="/v1/entries/{id} [DELETE]")

    # ── search tasks ──

    @task(4)
    @tag("search")
    def search_entries(self) -> None:
        self.client.get(
            "/v1/entries/search",
            params={"q": "load-test"},
            name="/v1/entries/search",
        )

    # ── tag tasks ──

    @task(3)
    @tag("tags")
    def create_tag(self) -> None:
        resp = self.client.post(
            "/v1/tags",
            json={"name": f"tag-{uuid.uuid4().hex[:6]}", "color": "#3b82f6"},
            name="/v1/tags [POST]",
        )
        if resp.status_code == 201:
            self.tag_ids.append(resp.json()["id"])

    @task(5)
    @tag("tags")
    def list_tags(self) -> None:
        self.client.get("/v1/tags", name="/v1/tags [GET]")

    @task(1)
    @tag("tags")
    def delete_tag(self) -> None:
        if not self.tag_ids:
            return
        tid = self.tag_ids.pop(0)
        self.client.delete(f"/v1/tags/{tid}", name="/v1/tags/{id} [DELETE]")

    # ── auth tasks ──

    @task(2)
    @tag("auth")
    def get_me(self) -> None:
        self.client.get("/v1/auth/me", name="/v1/auth/me")

    @task(1)
    @tag("auth")
    def refresh_token(self) -> None:
        resp = self.client.post(
            "/v1/auth/refresh",
            json={"refresh_token": getattr(self, "refresh_token", "")},
            name="/v1/auth/refresh",
        )
        if resp.status_code == 200:
            data = resp.json()
            self._set_auth(data["tokens"]["access_token"], data["tokens"]["refresh_token"])

    # ── health check ──

    @task(1)
    @tag("health")
    def health(self) -> None:
        self.client.get("/health", name="/health")
