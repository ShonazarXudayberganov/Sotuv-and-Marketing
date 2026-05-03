"""Sprint 1.3 — Telegram social account link + test send."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

# Force deterministic Telegram responses — no real API calls during tests.
os.environ["TELEGRAM_MOCK"] = "true"

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


async def _make_brand(client: AsyncClient, headers: dict, name: str = "Brand") -> str:
    resp = await client.post("/api/v1/brands", headers=headers, json={"name": name})
    return resp.json()["id"]


async def test_bot_info_returns_mocked_profile(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/social/telegram/bot-info", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mocked"] is True
    assert body["username"]


async def test_link_telegram_channel_creates_account(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")

    link = await client.post(
        "/api/v1/social/telegram/link",
        headers=headers,
        json={"brand_id": brand_id, "chat": "@akme_news"},
    )
    assert link.status_code == 201, link.text
    body = link.json()
    assert body["provider"] == "telegram"
    assert body["external_handle"] == "akme_news"
    assert body["external_name"]
    assert body["is_active"] is True


async def test_link_is_idempotent_for_same_chat(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    first = await client.post(
        "/api/v1/social/telegram/link",
        headers=headers,
        json={"brand_id": brand_id, "chat": "@same_channel"},
    )
    second = await client.post(
        "/api/v1/social/telegram/link",
        headers=headers,
        json={"brand_id": brand_id, "chat": "@same_channel"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    listing = await client.get(f"/api/v1/social/accounts?brand_id={brand_id}", headers=headers)
    assert listing.status_code == 200
    accounts = listing.json()
    assert len(accounts) == 1


async def test_send_test_message_returns_message_id(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    link = await client.post(
        "/api/v1/social/telegram/link",
        headers=headers,
        json={"brand_id": brand_id, "chat": "@akme_news"},
    )
    account_id = link.json()["id"]

    send = await client.post(
        "/api/v1/social/telegram/test",
        headers=headers,
        json={"account_id": account_id, "text": "Salom, NEXUS AI testdir."},
    )
    assert send.status_code == 200, send.text
    body = send.json()
    assert body["mocked"] is True
    assert body["sent_text"].startswith("Salom")
    assert body["message_id"] >= 0


async def test_unlink_account_removes_it(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    link = await client.post(
        "/api/v1/social/telegram/link",
        headers=headers,
        json={"brand_id": brand_id, "chat": "@throwaway"},
    )
    account_id = link.json()["id"]

    rm = await client.delete(f"/api/v1/social/accounts/{account_id}", headers=headers)
    assert rm.status_code == 200

    listing = await client.get(f"/api/v1/social/accounts?brand_id={brand_id}", headers=headers)
    assert listing.json() == []

    rm2 = await client.delete(f"/api/v1/social/accounts/{account_id}", headers=headers)
    assert rm2.status_code == 404


async def test_send_test_to_unknown_account_returns_404(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    fake_id = "00000000-0000-0000-0000-000000000000"
    send = await client.post(
        "/api/v1/social/telegram/test",
        headers=headers,
        json={"account_id": fake_id, "text": "hi"},
    )
    assert send.status_code == 404


async def test_accounts_filtered_by_brand(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_a = await _make_brand(client, headers, "Brand A")
    brand_b = await _make_brand(client, headers, "Brand B")

    for brand_id, chat in ((brand_a, "@a_news"), (brand_b, "@b_news")):
        await client.post(
            "/api/v1/social/telegram/link",
            headers=headers,
            json={"brand_id": brand_id, "chat": chat},
        )

    only_a = await client.get(f"/api/v1/social/accounts?brand_id={brand_a}", headers=headers)
    only_b = await client.get(f"/api/v1/social/accounts?brand_id={brand_b}", headers=headers)
    assert len(only_a.json()) == 1
    assert len(only_b.json()) == 1
    assert only_a.json()[0]["brand_id"] == brand_a
