"""Sprint 4.2 — Event hooks fire to outbound webhooks + provider sync."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

os.environ["WEBHOOK_MOCK"] = "true"
os.environ["MARKETPLACE_MOCK"] = "true"
os.environ["AI_MOCK"] = "true"

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


async def _create_outbound(
    client: AsyncClient, headers: dict, events: list[str]
) -> str:
    resp = await client.post(
        "/api/v1/marketplace/webhooks",
        headers=headers,
        json={
            "name": "Test sink",
            "direction": "out",
            "url": "https://example.com/sink",
            "events": events,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_contact_created_fires_outbound(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    eid = await _create_outbound(client, headers, ["contact.created"])

    await client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={"full_name": "Webhook Lead", "phone": "+998900099001"},
    )
    deliveries = (
        await client.get(
            f"/api/v1/marketplace/webhooks/{eid}/deliveries", headers=headers
        )
    ).json()
    assert any(
        d["event"] == "contact.created" and d["succeeded"] for d in deliveries
    )


async def test_deal_won_fires_outbound(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    eid = await _create_outbound(client, headers, ["deal.won"])

    contact = await client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={"full_name": "Big Customer", "phone": "+998900099002"},
    )
    deal = await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={
            "title": "Big deal",
            "contact_id": contact.json()["id"],
            "amount": 5_000_000,
        },
    )
    await client.post(
        f"/api/v1/crm/deals/{deal.json()['id']}/win", headers=headers
    )
    deliveries = (
        await client.get(
            f"/api/v1/marketplace/webhooks/{eid}/deliveries", headers=headers
        )
    ).json()
    assert any(d["event"] == "deal.won" for d in deliveries)


async def test_event_filter_skips_unsubscribed(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    eid = await _create_outbound(client, headers, ["deal.lost"])  # narrow subscription

    await client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={"full_name": "Skipped", "phone": "+998900099003"},
    )
    deliveries = (
        await client.get(
            f"/api/v1/marketplace/webhooks/{eid}/deliveries", headers=headers
        )
    ).json()
    assert not any(d["event"] == "contact.created" for d in deliveries)


async def test_sync_amocrm_imports_contacts(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post("/api/v1/marketplace/sync/amocrm", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "amocrm"
    assert body["pulled"] >= 1
    assert body["mocked"] is True

    # Mock provider returns 2 contacts; running sync again must not duplicate them.
    again = await client.post("/api/v1/marketplace/sync/amocrm", headers=headers)
    assert again.json()["pulled"] == 0


async def test_sync_bitrix24_imports_contacts(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post("/api/v1/marketplace/sync/bitrix24", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["pulled"] >= 1
    assert body["provider"] == "bitrix24"


async def test_sync_google_sheets_pushes_count(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={"full_name": "Sheet User", "phone": "+998900099005"},
    )
    resp = await client.post(
        "/api/v1/marketplace/sync/google_sheets", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["pushed"] >= 1


async def test_sync_unknown_provider_400(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post(
        "/api/v1/marketplace/sync/unicorn", headers=headers
    )
    assert resp.status_code == 400
