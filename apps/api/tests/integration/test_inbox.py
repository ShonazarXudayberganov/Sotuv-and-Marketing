"""Sprint 2.3 — Omnichannel inbox + AI auto-reply."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

os.environ["AI_MOCK"] = "true"
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


async def test_seed_mock_creates_conversations(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    seed = await client.post("/api/v1/inbox/seed-mock", headers=headers)
    assert seed.status_code == 200, seed.text
    assert seed.json()["inserted"] >= 3

    convs = (
        await client.get("/api/v1/inbox/conversations", headers=headers)
    ).json()
    # 3 mock messages but only 2 unique external_ids => 2 conversations
    assert len(convs) == 2
    assert all(c["channel"] == "telegram" for c in convs)


async def test_ingest_creates_thread_and_increments_unread(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    resp = await client.post(
        "/api/v1/inbox/ingest",
        headers=headers,
        json={
            "channel": "telegram",
            "external_id": "tg_user_42",
            "body": "Salom, bugun ish vaqtingiz qachon?",
            "title": "Test User",
            "auto_reply": False,
        },
    )
    assert resp.status_code == 201, resp.text

    convs = (
        await client.get("/api/v1/inbox/conversations", headers=headers)
    ).json()
    assert len(convs) == 1
    assert convs[0]["unread_count"] == 1
    assert "ish vaqti" in convs[0]["snippet"].lower()


async def test_outbound_message_persists_and_uses_mock_telegram(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post(
        "/api/v1/inbox/ingest",
        headers=headers,
        json={
            "channel": "telegram",
            "external_id": "tg_user_99",
            "body": "Salom",
            "auto_reply": False,
        },
    )
    cid = (
        (await client.get("/api/v1/inbox/conversations", headers=headers))
        .json()[0]["id"]
    )
    out = await client.post(
        f"/api/v1/inbox/conversations/{cid}/messages",
        headers=headers,
        json={"body": "Assalomu alaykum, qanday yordam beraman?"},
    )
    assert out.status_code == 201, out.text
    assert out.json()["direction"] == "out"

    msgs = (
        await client.get(
            f"/api/v1/inbox/conversations/{cid}/messages", headers=headers
        )
    ).json()
    assert len(msgs) == 2
    assert msgs[-1]["direction"] == "out"


async def test_mark_read_resets_unread_count(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post(
        "/api/v1/inbox/ingest",
        headers=headers,
        json={
            "channel": "telegram",
            "external_id": "unread_user",
            "body": "Test",
            "auto_reply": False,
        },
    )
    cid = (
        (await client.get("/api/v1/inbox/conversations", headers=headers))
        .json()[0]["id"]
    )
    read = await client.post(
        f"/api/v1/inbox/conversations/{cid}/read", headers=headers
    )
    assert read.json()["unread_count"] == 0


async def test_status_change_open_to_closed_back(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post(
        "/api/v1/inbox/ingest",
        headers=headers,
        json={
            "channel": "telegram",
            "external_id": "status_user",
            "body": "Hi",
            "auto_reply": False,
        },
    )
    cid = (
        (await client.get("/api/v1/inbox/conversations", headers=headers))
        .json()[0]["id"]
    )
    closed = await client.post(
        f"/api/v1/inbox/conversations/{cid}/status",
        headers=headers,
        json={"status": "closed"},
    )
    assert closed.json()["status"] == "closed"

    # New inbound auto-opens the closed thread
    await client.post(
        "/api/v1/inbox/ingest",
        headers=headers,
        json={
            "channel": "telegram",
            "external_id": "status_user",
            "body": "Yana savol",
            "auto_reply": False,
        },
    )
    refreshed = (
        await client.get(f"/api/v1/inbox/conversations/{cid}", headers=headers)
    ).json()
    assert refreshed["status"] == "open"


async def test_draft_reply_returns_mock_response(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post(
        "/api/v1/inbox/ingest",
        headers=headers,
        json={
            "channel": "telegram",
            "external_id": "ai_user",
            "body": "Salom! Yordam kerak edi.",
            "auto_reply": False,
        },
    )
    cid = (
        (await client.get("/api/v1/inbox/conversations", headers=headers))
        .json()[0]["id"]
    )
    draft = await client.post(
        f"/api/v1/inbox/conversations/{cid}/draft-reply", headers=headers
    )
    assert draft.status_code == 200, draft.text
    body = draft.json()
    assert body["reply"]
    assert 0 <= body["confidence"] <= 100
    assert body["mocked"] is True


async def test_auto_reply_config_round_trip(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    initial = (await client.get("/api/v1/inbox/auto-reply", headers=headers)).json()
    assert initial["is_enabled"] is False
    assert initial["confidence_threshold"] == 90

    upd = await client.patch(
        "/api/v1/inbox/auto-reply",
        headers=headers,
        json={
            "is_enabled": True,
            "confidence_threshold": 80,
            "channels_enabled": ["telegram", "instagram"],
        },
    )
    assert upd.status_code == 200
    assert upd.json()["is_enabled"] is True
    assert upd.json()["confidence_threshold"] == 80
    assert "telegram" in upd.json()["channels_enabled"]


async def test_auto_reply_fires_when_enabled_and_confident(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.patch(
        "/api/v1/inbox/auto-reply",
        headers=headers,
        json={
            "is_enabled": True,
            "confidence_threshold": 80,
            "channels_enabled": ["telegram"],
        },
    )

    # "Salom" → mock confidence 92, above threshold → auto-reply fires
    await client.post(
        "/api/v1/inbox/ingest",
        headers=headers,
        json={
            "channel": "telegram",
            "external_id": "auto_fire",
            "body": "Salom!",
            "auto_reply": True,
        },
    )
    cid = (
        (await client.get("/api/v1/inbox/conversations", headers=headers))
        .json()[0]["id"]
    )
    msgs = (
        await client.get(
            f"/api/v1/inbox/conversations/{cid}/messages", headers=headers
        )
    ).json()
    # one inbound + one auto-reply outbound
    assert len(msgs) == 2
    assert msgs[1]["direction"] == "out"
    assert msgs[1]["is_auto_reply"] is True
    assert msgs[1]["confidence"] >= 80


async def test_auto_reply_skipped_when_low_confidence(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.patch(
        "/api/v1/inbox/auto-reply",
        headers=headers,
        json={
            "is_enabled": True,
            "confidence_threshold": 90,
            "channels_enabled": ["telegram"],
        },
    )
    # "narx" → mock confidence 55 < 90 → no auto-reply
    await client.post(
        "/api/v1/inbox/ingest",
        headers=headers,
        json={
            "channel": "telegram",
            "external_id": "low_conf",
            "body": "Narx qancha?",
            "auto_reply": True,
        },
    )
    cid = (
        (await client.get("/api/v1/inbox/conversations", headers=headers))
        .json()[0]["id"]
    )
    msgs = (
        await client.get(
            f"/api/v1/inbox/conversations/{cid}/messages", headers=headers
        )
    ).json()
    assert len(msgs) == 1
    assert msgs[0]["direction"] == "in"


async def test_stats_summary(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post("/api/v1/inbox/seed-mock", headers=headers)
    stats = (await client.get("/api/v1/inbox/stats", headers=headers)).json()
    assert stats["total"] >= 1
    assert "telegram" in stats["by_channel"]
