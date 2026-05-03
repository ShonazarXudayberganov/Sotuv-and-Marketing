"""Sprint Foundation-close — audit/sessions/notification prefs/OAuth coverage."""

from __future__ import annotations

import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

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


# ─────────── Audit log GET ───────────


async def test_audit_log_lists_invite_action(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    invite = await client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "newhire@akme.uz",
            "phone": "+998909990001",
            "role_slug": "operator",
            "full_name": "New Hire",
        },
    )
    assert invite.status_code == 201, invite.text

    log = await client.get("/api/v1/audit", headers=headers)
    assert log.status_code == 200, log.text
    rows = log.json()
    actions = {r["action"] for r in rows}
    assert "users.invite" in actions


async def test_audit_log_filter_by_action(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "a@b.uz",
            "phone": "+998909990002",
            "role_slug": "viewer",
        },
    )
    log = await client.get("/api/v1/audit?action=users.invite", headers=headers)
    assert log.status_code == 200
    assert all(r["action"] == "users.invite" for r in log.json())


# ─────────── Notification preferences ───────────


async def test_notification_preferences_default_then_update(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    initial = await client.get("/api/v1/notifications/preferences", headers=headers)
    assert initial.status_code == 200, initial.text
    body = initial.json()
    assert "tasks" in body["channels"]

    upd = await client.put(
        "/api/v1/notifications/preferences",
        headers=headers,
        json={
            "channels": {"billing": ["email"]},
            "quiet_hours_start": 22,
            "quiet_hours_end": 7,
            "telegram_chat_id": "12345",
        },
    )
    assert upd.status_code == 200, upd.text
    out = upd.json()
    assert out["channels"]["billing"] == ["email"]
    assert out["quiet_hours_start"] == 22
    assert out["telegram_chat_id"] == "12345"


async def test_notification_preferences_rejects_unknown_category(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.put(
        "/api/v1/notifications/preferences",
        headers=headers,
        json={"channels": {"unknown_cat": ["email"]}},
    )
    assert resp.status_code == 422


# ─────────── User sessions ───────────


async def test_login_creates_session_listed_in_sessions_endpoint(
    client: AsyncClient, sample_register_payload: dict
):
    await _bootstrap(client, sample_register_payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email_or_phone": sample_register_payload["email"],
            "password": sample_register_payload["password"],
        },
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    sessions = await client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions.status_code == 200, sessions.text
    rows = sessions.json()
    # bootstrap login + this explicit login = at least 2 active sessions
    assert len(rows) >= 2


async def test_revoked_session_blocks_refresh(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": bundle["refresh_token"]},
    )
    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": bundle["refresh_token"]},
    )
    assert refresh.status_code == 401

    # Sessions endpoint should still work with the (still-valid) access token
    sessions = await client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    # The bootstrap session must now appear with no active rows
    assert sessions.json() == []


async def test_revoke_session_via_endpoint(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    sessions = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
    assert sessions
    target = sessions[0]["id"]
    rm = await client.delete(f"/api/v1/auth/sessions/{target}", headers=headers)
    assert rm.status_code == 204


# ─────────── OAuth (mock mode) ───────────


async def test_google_oauth_creates_tenant(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/google",
        json={"id_token": "mock:owner@google.uz:Google Demo"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_new_user"] is True
    assert body["user"]["email"] == "owner@google.uz"
    assert body["tenant"]["schema_name"].startswith("tenant_")


async def test_google_oauth_returns_existing_user(client: AsyncClient):
    first = await client.post(
        "/api/v1/auth/google",
        json={"id_token": "mock:repeat@google.uz:Repeat"},
    )
    assert first.status_code == 200
    second = await client.post(
        "/api/v1/auth/google",
        json={"id_token": "mock:repeat@google.uz:Repeat"},
    )
    assert second.status_code == 200
    assert second.json()["is_new_user"] is False
    assert second.json()["user"]["id"] == first.json()["user"]["id"]


async def test_telegram_oauth_creates_tenant(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/telegram",
        json={"mock_token": "mock:tg_user@telegram.nexusai.uz:Telegram User"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["email"] == "tg_user@telegram.nexusai.uz"
    assert body["tenant"]["schema_name"].startswith("tenant_")
