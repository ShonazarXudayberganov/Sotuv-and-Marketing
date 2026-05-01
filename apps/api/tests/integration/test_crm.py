"""Sprint 2.1 — CRM contacts: CRUD, search, AI score, activity timeline."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

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


async def _make_contact(
    client: AsyncClient, headers: dict, name: str = "Akmal", **extra
) -> dict:
    payload = {
        "full_name": name,
        "phone": "+998901112233",
        "email": "akmal@example.com",
        "status": "lead",
        **extra,
    }
    resp = await client.post("/api/v1/crm/contacts", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_contact_initialises_score(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact = await _make_contact(client, headers, name="Akmal Karimov")
    assert contact["full_name"] == "Akmal Karimov"
    assert contact["status"] == "lead"
    assert contact["ai_score"] > 0
    assert contact["ai_score_reason"]


async def test_search_filters_contacts_by_query(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _make_contact(
        client,
        headers,
        name="Akmal Karimov",
        phone="+998900001111",
        email="akmal@a.uz",
    )
    await _make_contact(
        client,
        headers,
        name="Bobur Nazarov",
        phone="+998900002222",
        email="bobur@b.uz",
    )

    only_akmal = (
        await client.get("/api/v1/crm/contacts?query=Akmal", headers=headers)
    ).json()
    only_phone = (
        await client.get("/api/v1/crm/contacts?query=0001111", headers=headers)
    ).json()
    assert len(only_akmal) == 1
    assert only_akmal[0]["full_name"] == "Akmal Karimov"
    assert len(only_phone) == 1


async def test_status_filter_and_min_score(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    lead = await _make_contact(client, headers, name="Lead One", status="lead")
    customer = await _make_contact(
        client, headers, name="Big Customer", status="customer"
    )

    leads = (
        await client.get("/api/v1/crm/contacts?status=lead", headers=headers)
    ).json()
    customers = (
        await client.get("/api/v1/crm/contacts?status=customer", headers=headers)
    ).json()
    assert any(c["id"] == lead["id"] for c in leads)
    assert any(c["id"] == customer["id"] for c in customers)

    high = (
        await client.get(
            f"/api/v1/crm/contacts?min_score={customer['ai_score']}",
            headers=headers,
        )
    ).json()
    assert all(c["ai_score"] >= customer["ai_score"] for c in high)


async def test_update_changes_status_and_rescore(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact = await _make_contact(client, headers, name="Update Me", status="lead")
    initial = contact["ai_score"]

    upd = await client.patch(
        f"/api/v1/crm/contacts/{contact['id']}",
        headers=headers,
        json={"status": "customer", "tags": ["vip"]},
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "customer"
    assert upd.json()["ai_score"] >= initial


async def test_delete_contact_removes_it(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact = await _make_contact(client, headers, name="Delete Me")
    rm = await client.delete(
        f"/api/v1/crm/contacts/{contact['id']}", headers=headers
    )
    assert rm.status_code == 200
    rm2 = await client.delete(
        f"/api/v1/crm/contacts/{contact['id']}", headers=headers
    )
    assert rm2.status_code == 404


async def test_add_activity_bumps_score(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact = await _make_contact(client, headers, name="Active Lead")
    initial_score = contact["ai_score"]

    act = await client.post(
        f"/api/v1/crm/contacts/{contact['id']}/activities",
        headers=headers,
        json={
            "kind": "call_in",
            "title": "Birinchi qo'ng'iroq",
            "channel": "phone",
            "direction": "in",
            "duration_seconds": 240,
        },
    )
    assert act.status_code == 201
    assert act.json()["kind"] == "call_in"

    refreshed = (
        await client.get(f"/api/v1/crm/contacts/{contact['id']}", headers=headers)
    ).json()
    assert refreshed["ai_score"] > initial_score

    timeline = (
        await client.get(
            f"/api/v1/crm/contacts/{contact['id']}/activities", headers=headers
        )
    ).json()
    assert len(timeline) == 1


async def test_rescore_endpoint_returns_score(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact = await _make_contact(client, headers, name="Rescore Me")
    resp = await client.post(
        f"/api/v1/crm/contacts/{contact['id']}/rescore", headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert 0 <= body["score"] <= 100
    assert body["reason"]


async def test_stats_groups_by_status(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _make_contact(client, headers, name="L1", status="lead")
    await _make_contact(client, headers, name="L2", status="lead")
    await _make_contact(client, headers, name="C1", status="customer")
    stats = (await client.get("/api/v1/crm/contacts/stats", headers=headers)).json()
    assert stats["total"] == 3
    assert stats["by_status"]["lead"] == 2
    assert stats["by_status"]["customer"] == 1


async def test_unknown_contact_returns_404(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    fake = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/v1/crm/contacts/{fake}", headers=headers)
    assert resp.status_code == 404
