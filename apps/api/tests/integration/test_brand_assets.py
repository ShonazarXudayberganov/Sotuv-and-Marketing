"""Brand assets CRUD/upload endpoints."""

from __future__ import annotations

import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

pytestmark = pytest.mark.asyncio


def _code_for(phone: str) -> str:
    for sent_phone, message in MockSMSProvider.sent:
        if sent_phone == phone:
            match = re.search(r"\b(\d{4,8})\b", message)
            if match:
                return match.group(1)
    raise AssertionError(f"No SMS sent to {phone}")


async def _bootstrap(client: AsyncClient, payload: dict) -> tuple[dict[str, str], str]:
    reg = await client.post("/api/v1/auth/register", json=payload)
    code = _code_for(payload["phone"])
    verify = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    bundle = verify.json()
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand = await client.post(
        "/api/v1/brands",
        headers=headers,
        json={"name": "Akme Beauty", "is_default": True},
    )
    return headers, brand.json()["id"]


async def test_upload_asset_and_list_by_brand(client: AsyncClient, sample_register_payload: dict):
    headers, brand_id = await _bootstrap(client, sample_register_payload)

    upload = await client.post(
        "/api/v1/brand-assets/upload",
        headers=headers,
        data={
            "brand_id": brand_id,
            "asset_type": "logo",
            "name": "Primary logo",
            "is_primary": "true",
        },
        files={"file": ("logo.png", b"\x89PNG\r\n", "image/png")},
    )
    assert upload.status_code == 201, upload.text
    body = upload.json()
    assert body["brand_id"] == brand_id
    assert body["asset_type"] == "logo"
    assert body["file_url"].startswith("data:image/png;base64,")
    assert body["metadata"]["filename"] == "logo.png"
    assert body["is_primary"] is True

    listing = await client.get(f"/api/v1/brands/{brand_id}/assets", headers=headers)
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [body["id"]]


async def test_primary_asset_is_unique_per_brand_and_type(
    client: AsyncClient, sample_register_payload: dict
):
    headers, brand_id = await _bootstrap(client, sample_register_payload)

    first = await client.post(
        "/api/v1/brand-assets",
        headers=headers,
        json={
            "brand_id": brand_id,
            "asset_type": "color",
            "name": "Green",
            "metadata": {"hex": "#16a34a"},
            "is_primary": True,
        },
    )
    second = await client.post(
        "/api/v1/brand-assets",
        headers=headers,
        json={
            "brand_id": brand_id,
            "asset_type": "color",
            "name": "Blue",
            "metadata": {"hex": "#2563eb"},
            "is_primary": True,
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201

    listing = (
        await client.get(
            "/api/v1/brand-assets",
            headers=headers,
            params={"brand_id": brand_id, "asset_type": "color"},
        )
    ).json()
    by_id = {item["id"]: item for item in listing}
    assert by_id[first.json()["id"]]["is_primary"] is False
    assert by_id[second.json()["id"]]["is_primary"] is True


async def test_update_and_delete_asset(client: AsyncClient, sample_register_payload: dict):
    headers, brand_id = await _bootstrap(client, sample_register_payload)

    create = await client.post(
        "/api/v1/brand-assets",
        headers=headers,
        json={
            "brand_id": brand_id,
            "asset_type": "reference",
            "name": "Moodboard",
            "file_url": "https://example.com/moodboard",
        },
    )
    asset_id = create.json()["id"]

    update = await client.patch(
        f"/api/v1/brand-assets/{asset_id}",
        headers=headers,
        json={"name": "Spring moodboard", "metadata": {"notes": "soft light"}},
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Spring moodboard"
    assert update.json()["metadata"]["notes"] == "soft light"

    delete = await client.delete(f"/api/v1/brands/{brand_id}/assets/{asset_id}", headers=headers)
    assert delete.status_code == 200
    listing = await client.get(f"/api/v1/brands/{brand_id}/assets", headers=headers)
    assert listing.json() == []


async def test_rejects_unsupported_asset_type(client: AsyncClient, sample_register_payload: dict):
    headers, brand_id = await _bootstrap(client, sample_register_payload)

    resp = await client.post(
        "/api/v1/brand-assets",
        headers=headers,
        json={"brand_id": brand_id, "asset_type": "unknown", "name": "Bad"},
    )
    assert resp.status_code == 400
    assert "Allowed" in resp.json()["detail"]
