"""
Integration tests for attachment endpoints.

S3 operations are mocked — tests verify API logic, DB persistence, and validation.
"""

import io
import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

# ── Helpers ──


async def _register_and_login(client: AsyncClient, email: str = "att@test.com") -> dict:
    """Register a user and return auth headers."""
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "TestPass123", "display_name": "Tester"},
    )
    resp = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "TestPass123"},
    )
    token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_entry(client: AsyncClient, headers: dict) -> dict:
    """Create a diary entry and return its response data."""
    resp = await client.post(
        "/v1/entries",
        headers=headers,
        json={"body": "Entry for attachment tests."},
    )
    return resp.json()


async def _upload_file(
    client: AsyncClient,
    entry_id: str,
    headers: dict,
    filename: str = "photo.jpg",
    content_type: str = "image/jpeg",
    content: bytes = b"fake-image-data",
):
    """Upload a file attachment to an entry."""
    return await client.post(
        f"/v1/entries/{entry_id}/attachments",
        headers=headers,
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


# ── Fixtures ──


@pytest.fixture
def mock_s3():
    """Mock all S3 client operations."""
    with (
        patch("app.services.s3_client.upload_file") as mock_upload,
        patch("app.services.s3_client.generate_presigned_url") as mock_presign,
        patch("app.services.s3_client.delete_file") as mock_delete,
    ):
        mock_presign.return_value = "https://s3.example.com/presigned-url"
        yield {
            "upload": mock_upload,
            "presign": mock_presign,
            "delete": mock_delete,
        }


# ── Upload Tests ──


@pytest.mark.asyncio
async def test_upload_image_attachment(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)

    resp = await _upload_file(client, entry["id"], headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["entry_id"] == entry["id"]
    assert data["file_name"] == "photo.jpg"
    assert data["file_type"] == "image/jpeg"
    assert data["file_size"] == len(b"fake-image-data")
    assert data["download_url"] == "https://s3.example.com/presigned-url"
    mock_s3["upload"].assert_called_once()


@pytest.mark.asyncio
async def test_upload_pdf_attachment(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)

    resp = await _upload_file(
        client,
        entry["id"],
        headers,
        filename="doc.pdf",
        content_type="application/pdf",
        content=b"fake-pdf",
    )

    assert resp.status_code == 201
    assert resp.json()["file_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_upload_png_attachment(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)

    resp = await _upload_file(
        client,
        entry["id"],
        headers,
        filename="image.png",
        content_type="image/png",
    )

    assert resp.status_code == 201
    assert resp.json()["file_type"] == "image/png"


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)

    resp = await _upload_file(
        client,
        entry["id"],
        headers,
        filename="script.sh",
        content_type="text/x-shellscript",
        content=b"#!/bin/bash",
    )

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_FILE_TYPE"
    mock_s3["upload"].assert_not_called()


@pytest.mark.asyncio
async def test_upload_file_too_large(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)

    with patch("app.services.attachment_service.MAX_FILE_SIZE", 100):
        resp = await _upload_file(
            client,
            entry["id"],
            headers,
            content=b"x" * 101,
        )

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "FILE_TOO_LARGE"
    mock_s3["upload"].assert_not_called()


@pytest.mark.asyncio
async def test_upload_to_nonexistent_entry(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    fake_id = str(uuid.uuid4())

    resp = await _upload_file(client, fake_id, headers)

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_to_other_users_entry(client: AsyncClient, mock_s3):
    headers1 = await _register_and_login(client, email="user1_att@test.com")
    headers2 = await _register_and_login(client, email="user2_att@test.com")
    entry = await _create_entry(client, headers1)

    resp = await _upload_file(client, entry["id"], headers2)

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_upload_unauthenticated(client: AsyncClient, mock_s3):
    resp = await client.post(
        f"/v1/entries/{uuid.uuid4()}/attachments",
        files={"file": ("f.jpg", io.BytesIO(b"data"), "image/jpeg")},
    )
    assert resp.status_code == 401


# ── List Tests ──


@pytest.mark.asyncio
async def test_list_attachments(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)

    await _upload_file(client, entry["id"], headers, filename="a.jpg")
    await _upload_file(client, entry["id"], headers, filename="b.png", content_type="image/png")

    resp = await client.get(f"/v1/entries/{entry['id']}/attachments", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["attachments"]) == 2
    names = {att["file_name"] for att in data["attachments"]}
    assert names == {"a.jpg", "b.png"}
    assert all(att["download_url"] for att in data["attachments"])


@pytest.mark.asyncio
async def test_list_attachments_empty(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)

    resp = await client.get(f"/v1/entries/{entry['id']}/attachments", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["attachments"] == []


@pytest.mark.asyncio
async def test_list_attachments_other_users_entry(client: AsyncClient, mock_s3):
    headers1 = await _register_and_login(client, email="listuser1@test.com")
    headers2 = await _register_and_login(client, email="listuser2@test.com")
    entry = await _create_entry(client, headers1)

    resp = await client.get(f"/v1/entries/{entry['id']}/attachments", headers=headers2)

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_attachments_unauthenticated(client: AsyncClient, mock_s3):
    resp = await client.get(f"/v1/entries/{uuid.uuid4()}/attachments")
    assert resp.status_code == 401


# ── Delete Tests ──


@pytest.mark.asyncio
async def test_delete_attachment(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)
    upload_resp = await _upload_file(client, entry["id"], headers)
    attachment_id = upload_resp.json()["id"]

    resp = await client.delete(f"/v1/attachments/{attachment_id}", headers=headers)

    assert resp.status_code == 204
    mock_s3["delete"].assert_called_once()

    # Verify it's gone from the list
    list_resp = await client.get(f"/v1/entries/{entry['id']}/attachments", headers=headers)
    assert len(list_resp.json()["attachments"]) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_attachment(client: AsyncClient, mock_s3):
    headers = await _register_and_login(client)

    resp = await client.delete(f"/v1/attachments/{uuid.uuid4()}", headers=headers)

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_other_users_attachment(client: AsyncClient, mock_s3):
    headers1 = await _register_and_login(client, email="deluser1@test.com")
    headers2 = await _register_and_login(client, email="deluser2@test.com")
    entry = await _create_entry(client, headers1)
    upload_resp = await _upload_file(client, entry["id"], headers1)
    attachment_id = upload_resp.json()["id"]

    resp = await client.delete(f"/v1/attachments/{attachment_id}", headers=headers2)

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_unauthenticated(client: AsyncClient, mock_s3):
    resp = await client.delete(f"/v1/attachments/{uuid.uuid4()}")
    assert resp.status_code == 401


# ── Edge Cases ──


@pytest.mark.asyncio
async def test_filename_sanitization(client: AsyncClient, mock_s3):
    """Filenames with path components should be stripped to just the name."""
    headers = await _register_and_login(client)
    entry = await _create_entry(client, headers)

    resp = await _upload_file(
        client,
        entry["id"],
        headers,
        filename="../../etc/passwd.jpg",
    )

    assert resp.status_code == 201
    assert resp.json()["file_name"] == "passwd.jpg"
