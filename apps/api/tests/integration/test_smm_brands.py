"""Sprint 1.1 — brands + integration credentials."""

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


async def _bootstrap(client: AsyncClient, payload: dict) -> dict:
    reg = await client.post("/api/v1/auth/register", json=payload)
    code = _code_for(payload["phone"])
    verify = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    return verify.json()


# ─────────── Brands ───────────


async def test_owner_creates_first_brand_and_lists_it(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    create = await client.post(
        "/api/v1/brands",
        headers=headers,
        json={
            "name": "Akme Beauty",
            "industry": "salon-klinika",
            "voice_tone": "Iliq, professional, ehtiyotkor",
            "languages": ["uz", "ru"],
            "is_default": True,
        },
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["slug"].startswith("akme")
    assert body["is_default"] is True

    listing = await client.get("/api/v1/brands", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_brand_slug_uniqueness(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    a = await client.post("/api/v1/brands", headers=headers, json={"name": "Brand A"})
    b = await client.post("/api/v1/brands", headers=headers, json={"name": "Brand A"})
    assert a.json()["slug"] == "brand-a"
    assert b.json()["slug"] == "brand-a-1"


async def test_set_default_swaps_old_default(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    a = await client.post(
        "/api/v1/brands", headers=headers, json={"name": "First", "is_default": True}
    )
    b = await client.post("/api/v1/brands", headers=headers, json={"name": "Second"})
    a_id = a.json()["id"]
    b_id = b.json()["id"]

    swap = await client.post(f"/api/v1/brands/{b_id}/set-default", headers=headers)
    assert swap.status_code == 200
    assert swap.json()["is_default"] is True

    listing = (await client.get("/api/v1/brands", headers=headers)).json()
    by_id = {br["id"]: br for br in listing}
    assert by_id[b_id]["is_default"] is True
    assert by_id[a_id]["is_default"] is False


async def test_update_and_delete_brand(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    create = await client.post("/api/v1/brands", headers=headers, json={"name": "Demo"})
    bid = create.json()["id"]

    upd = await client.patch(
        f"/api/v1/brands/{bid}", headers=headers, json={"description": "New desc"}
    )
    assert upd.json()["description"] == "New desc"

    rm = await client.delete(f"/api/v1/brands/{bid}", headers=headers)
    assert rm.status_code == 200
    listing = (await client.get("/api/v1/brands", headers=headers)).json()
    assert listing == []


# ─────────── Integrations ───────────


async def test_list_integrations_shows_all_providers_disconnected(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    resp = await client.get("/api/v1/integrations", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    providers = {item["provider"] for item in items}
    assert {"anthropic", "openai", "telegram_bot", "meta_app"} <= providers
    assert all(item["connected"] is False for item in items)


async def test_connect_anthropic_then_disconnect(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    connect = await client.put(
        "/api/v1/integrations/anthropic",
        headers=headers,
        json={"label": "Production", "credentials": {"api_key": "sk-ant-test12345"}},
    )
    assert connect.status_code == 200, connect.text
    body = connect.json()
    assert body["connected"] is True
    assert body["masked_values"]["api_key"].endswith("2345")
    assert "sk-ant" not in body["masked_values"]["api_key"]

    items = (await client.get("/api/v1/integrations", headers=headers)).json()
    anthro = next(i for i in items if i["provider"] == "anthropic")
    assert anthro["connected"] is True

    disc = await client.delete("/api/v1/integrations/anthropic", headers=headers)
    assert disc.status_code == 200
    items = (await client.get("/api/v1/integrations", headers=headers)).json()
    anthro = next(i for i in items if i["provider"] == "anthropic")
    assert anthro["connected"] is False


async def test_connect_unknown_provider_404(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    resp = await client.put(
        "/api/v1/integrations/unknown_xyz",
        headers=headers,
        json={"credentials": {"api_key": "x"}},
    )
    assert resp.status_code == 404


async def test_connect_missing_required_fields_400(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    resp = await client.put(
        "/api/v1/integrations/meta_app",
        headers=headers,
        json={"credentials": {"app_id": "123"}},  # missing app_secret + page_access_token
    )
    assert resp.status_code == 400
    assert "missing" in resp.json()["detail"].lower()
