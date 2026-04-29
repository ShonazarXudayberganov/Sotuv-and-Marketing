"""Integration tests for Sprint 4 — tasks, 2FA, API keys, notifications."""

from __future__ import annotations

import re

import pyotp
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


async def _bootstrap(client: AsyncClient, payload: dict) -> dict:
    reg = await client.post("/api/v1/auth/register", json=payload)
    code = _code_for(payload["phone"])
    verify = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    return verify.json()


async def test_create_list_update_delete_task(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    create = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Bitim yopish", "priority": "high"},
    )
    assert create.status_code == 201, create.text
    task_id = create.json()["id"]

    listing = await client.get("/api/v1/tasks", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    update = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"status": "done"},
    )
    assert update.status_code == 200
    assert update.json()["status"] == "done"
    assert update.json()["completed_at"] is not None

    delete = await client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert delete.status_code == 200

    listing2 = await client.get("/api/v1/tasks", headers=headers)
    assert listing2.json() == []


async def test_task_filtering_by_status(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    for status in ["new", "in_progress", "done"]:
        await client.post(
            "/api/v1/tasks", headers=headers, json={"title": f"Test {status}", "status": status}
        )
    new_only = await client.get("/api/v1/tasks?status=new", headers=headers)
    assert len(new_only.json()) == 1
    assert new_only.json()[0]["status"] == "new"


async def test_2fa_setup_and_verify(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    setup = await client.post("/api/v1/2fa/setup", headers=headers)
    assert setup.status_code == 200
    body = setup.json()
    assert body["secret"]
    assert body["qr_data_url"].startswith("data:image/png;base64,")
    assert len(body["backup_codes"]) == 8

    code = pyotp.TOTP(body["secret"]).now()
    verify = await client.post("/api/v1/2fa/verify", headers=headers, json={"code": code})
    assert verify.status_code == 200
    assert verify.json()["enabled"] is True


async def test_2fa_rejects_wrong_code(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post("/api/v1/2fa/setup", headers=headers)
    resp = await client.post("/api/v1/2fa/verify", headers=headers, json={"code": "000000"})
    assert resp.status_code == 400


async def test_api_key_create_list_revoke(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    create = await client.post(
        "/api/v1/api-keys",
        headers=headers,
        json={"name": "CI bot", "scopes": ["tasks.read"], "rate_limit_per_minute": 30},
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["plaintext_key"].startswith("nxa_")
    assert body["key_prefix"].startswith("nxa_")

    listing = await client.get("/api/v1/api-keys", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    revoke = await client.post(f"/api/v1/api-keys/{body['id']}/revoke", headers=headers)
    assert revoke.status_code == 200
    after = await client.get("/api/v1/api-keys", headers=headers)
    assert after.json()[0]["revoked_at"] is not None


async def test_notifications_list_starts_empty_and_mark_read(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    listing = await client.get("/api/v1/notifications", headers=headers)
    assert listing.status_code == 200
    assert listing.json() == []

    mark = await client.post("/api/v1/notifications/mark-all-read", headers=headers)
    assert mark.status_code == 200
    assert mark.json() == {"marked": 0}
