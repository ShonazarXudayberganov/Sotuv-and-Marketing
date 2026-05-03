"""Sprint 4.1 — Marketplace catalog + webhook endpoints (HMAC + outbound)."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider
from app.services.webhook_service import sign

os.environ["WEBHOOK_MOCK"] = "true"

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


async def test_catalog_lists_all_providers(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    catalog = (await client.get("/api/v1/marketplace/catalog", headers=headers)).json()
    keys = {p["provider"] for p in catalog}
    # Sprint 1 providers + new Sprint 4.1 ones
    assert {"anthropic", "telegram_bot", "amocrm", "bitrix24", "onec", "google_sheets"}.issubset(
        keys
    )
    crm_providers = [p for p in catalog if p["category"] == "crm"]
    assert len(crm_providers) >= 2  # amocrm + bitrix24


async def test_create_outbound_webhook_returns_secret_once(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={
            "name": "Slack notifications",
            "direction": "out",
            "url": "https://hooks.slack.com/services/T/B/X",
            "events": ["deal.won", "post.published"],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["direction"] == "out"
    assert body["secret"]  # returned ONCE on creation
    assert body["events"] == ["deal.won", "post.published"]
    # Subsequent listing should not include secret
    listing = (await client.get("/api/v1/marketplace/webhooks", headers=headers)).json()
    assert "secret" not in listing[0]


async def test_outbound_webhook_requires_url(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={"name": "No url", "direction": "out"},
    )
    assert resp.status_code == 400


async def test_unknown_event_rejected(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={
            "name": "bad",
            "direction": "out",
            "url": "https://x",
            "events": ["nonexistent.event"],
        },
    )
    assert resp.status_code == 400


async def test_test_outbound_records_delivery(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    create = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={
            "name": "Test outbound",
            "direction": "out",
            "url": "https://example.com/hook",
            "events": ["deal.won"],
        },
    )
    assert create.status_code == 201, create.text
    eid = create.json()["id"]
    resp = await client.post(
        f"/api/v1/marketplace/webhooks/{eid}/test",
        headers=headers,
        json={"event": "deal.won", "payload": {"deal_id": "x", "amount": 1000000}},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["succeeded"] is True
    assert body["status_code"] == 200

    deliveries = (
        await client.get(f"/api/v1/marketplace/webhooks/{eid}/deliveries", headers=headers)
    ).json()
    assert len(deliveries) == 1


async def test_inbound_webhook_with_valid_signature(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    create = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={"name": "Inbound", "direction": "in"},
    )
    eid = create.json()["id"]
    secret = create.json()["secret"]

    raw = b'{"order_id": 42, "amount": 1500000}'
    sig = sign(secret, raw)
    resp = await client.post(
        f"/api/v1/marketplace/webhooks/in/{eid}",
        headers={
            **headers,
            "Content-Type": "application/json",
            "X-Nexus-Signature": sig,
            "X-Nexus-Event": "order.created",
        },
        content=raw,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["received"] is True


async def test_inbound_webhook_with_invalid_signature(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    create = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={"name": "Inbound2", "direction": "in"},
    )
    eid = create.json()["id"]

    resp = await client.post(
        f"/api/v1/marketplace/webhooks/in/{eid}",
        headers={
            **headers,
            "Content-Type": "application/json",
            "X-Nexus-Signature": "bad-signature",
        },
        content=b'{"hi": 1}',
    )
    assert resp.status_code == 401


async def test_rotate_secret_invalidates_old(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    create = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={"name": "Rotate me", "direction": "in"},
    )
    eid = create.json()["id"]
    old_secret = create.json()["secret"]

    rotated = await client.post(
        f"/api/v1/marketplace/webhooks/{eid}/rotate-secret", headers=headers
    )
    assert rotated.status_code == 200
    new_secret = rotated.json()["secret"]
    assert old_secret != new_secret

    raw = b'{"x":1}'
    bad = await client.post(
        f"/api/v1/marketplace/webhooks/in/{eid}",
        headers={**headers, "X-Nexus-Signature": sign(old_secret, raw)},
        content=raw,
    )
    assert bad.status_code == 401


async def test_toggle_disables_inbound(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    create = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={"name": "Off", "direction": "in"},
    )
    eid = create.json()["id"]
    secret = create.json()["secret"]

    off = await client.post(
        f"/api/v1/marketplace/webhooks/{eid}/toggle?active=false", headers=headers
    )
    assert off.json()["is_active"] is False

    raw = b'{"x":1}'
    blocked = await client.post(
        f"/api/v1/marketplace/webhooks/in/{eid}",
        headers={**headers, "X-Nexus-Signature": sign(secret, raw)},
        content=raw,
    )
    assert blocked.status_code == 403


async def test_delete_webhook(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    create = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={
            "name": "Delete me",
            "direction": "out",
            "url": "https://example.com/del",
        },
    )
    eid = create.json()["id"]
    rm = await client.delete(f"/api/v1/marketplace/webhooks/{eid}", headers=headers)
    assert rm.status_code == 200
    rm2 = await client.delete(f"/api/v1/marketplace/webhooks/{eid}", headers=headers)
    assert rm2.status_code == 404
