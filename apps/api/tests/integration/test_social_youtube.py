"""Sprint 1.5 — YouTube channel link + stats."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

# Force deterministic YouTube responses — no real API calls during tests.
os.environ["YOUTUBE_MOCK"] = "true"

pytestmark = pytest.mark.asyncio


def _code_for(phone: str) -> str:
    for sent_phone, message in reversed(MockSMSProvider.sent):
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


async def test_lookup_returns_channel_with_stats(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/social/youtube/lookup?handle=@akme", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mocked"] is True
    assert body["id"].startswith("UC")
    assert body["subscribers"] > 0
    assert body["videos"] > 0


async def test_lookup_without_handle_or_id_returns_400(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/social/youtube/lookup", headers=headers)
    assert resp.status_code == 400


async def test_link_youtube_channel_creates_account(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")

    link = await client.post(
        "/api/v1/social/youtube/link",
        headers=headers,
        json={"brand_id": brand_id, "handle": "@akme"},
    )
    assert link.status_code == 201, link.text
    body = link.json()
    assert body["provider"] == "youtube"
    assert body["chat_type"] == "channel"
    assert body["external_id"].startswith("UC")


async def test_link_is_idempotent_for_same_channel(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    first = await client.post(
        "/api/v1/social/youtube/link",
        headers=headers,
        json={"brand_id": brand_id, "handle": "@same"},
    )
    second = await client.post(
        "/api/v1/social/youtube/link",
        headers=headers,
        json={"brand_id": brand_id, "handle": "@same"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


async def test_stats_returns_recent_videos(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    link = await client.post(
        "/api/v1/social/youtube/link",
        headers=headers,
        json={"brand_id": brand_id, "handle": "@akme"},
    )
    account_id = link.json()["id"]

    stats = await client.get(f"/api/v1/social/youtube/{account_id}/stats?limit=4", headers=headers)
    assert stats.status_code == 200, stats.text
    body = stats.json()
    assert body["mocked"] is True
    assert body["account_id"] == account_id
    assert body["subscribers"] > 0
    assert len(body["recent"]) == 4
    first = body["recent"][0]
    assert first["view_count"] >= 0
    assert first["thumbnail_url"]


async def test_stats_for_unknown_account_returns_404(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    fake_id = "00000000-0000-0000-0000-000000000000"
    stats = await client.get(f"/api/v1/social/youtube/{fake_id}/stats", headers=headers)
    assert stats.status_code == 404


async def test_stats_for_telegram_account_returns_404(
    client: AsyncClient, sample_register_payload: dict
):
    """The endpoint must not return YouTube stats for non-YouTube accounts."""
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    # Pre-existing helper: link a Telegram account
    os.environ["TELEGRAM_MOCK"] = "true"
    tg = await client.post(
        "/api/v1/social/telegram/link",
        headers=headers,
        json={"brand_id": brand_id, "chat": "@x"},
    )
    tg_id = tg.json()["id"]
    stats = await client.get(f"/api/v1/social/youtube/{tg_id}/stats", headers=headers)
    assert stats.status_code == 404
