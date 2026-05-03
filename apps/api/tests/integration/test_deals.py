"""Sprint 2.2 — Deals + multi-pipeline."""

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


async def _make_contact(client: AsyncClient, headers: dict, name: str) -> str:
    resp = await client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={"full_name": name, "status": "lead"},
    )
    return resp.json()["id"]


async def test_default_pipeline_seeded_with_seven_stages(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    pipelines = (await client.get("/api/v1/crm/pipelines", headers=headers)).json()
    assert len(pipelines) == 1
    assert pipelines[0]["is_default"] is True
    assert pipelines[0]["slug"] == "main"
    stages = pipelines[0]["stages"]
    assert len(stages) == 7
    slugs = [s["slug"] for s in stages]
    assert slugs == [
        "new",
        "contacted",
        "negotiation",
        "proposal",
        "agreed",
        "won",
        "lost",
    ]
    assert any(s["is_won"] for s in stages)
    assert any(s["is_lost"] for s in stages)


async def test_create_deal_uses_default_pipeline_and_first_stage(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Lead One")

    resp = await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={
            "title": "Birinchi bitim",
            "contact_id": contact_id,
            "amount": 5_000_000,
            "currency": "UZS",
        },
    )
    assert resp.status_code == 201, resp.text
    deal = resp.json()
    assert deal["status"] == "open"
    assert deal["probability"] == 10  # first stage default
    assert deal["amount"] == 5_000_000
    assert deal["currency"] == "UZS"


async def test_move_to_stage_syncs_probability_and_logs_activity(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Active Lead")
    pipelines = (await client.get("/api/v1/crm/pipelines", headers=headers)).json()
    stages = pipelines[0]["stages"]
    proposal = next(s for s in stages if s["slug"] == "proposal")

    create = await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={"title": "Mid funnel", "contact_id": contact_id, "amount": 1_000_000},
    )
    deal_id = create.json()["id"]

    move = await client.patch(
        f"/api/v1/crm/deals/{deal_id}",
        headers=headers,
        json={"stage_id": proposal["id"]},
    )
    assert move.status_code == 200
    assert move.json()["stage_id"] == proposal["id"]
    assert move.json()["probability"] == 60

    timeline = (
        await client.get(f"/api/v1/crm/contacts/{contact_id}/activities", headers=headers)
    ).json()
    assert any(a["kind"] == "status_change" for a in timeline)


async def test_win_deal_closes_it(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Winner")

    create = await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={"title": "Closing", "contact_id": contact_id, "amount": 2_000_000},
    )
    deal_id = create.json()["id"]

    win = await client.post(f"/api/v1/crm/deals/{deal_id}/win", headers=headers)
    assert win.status_code == 200
    body = win.json()
    assert body["status"] == "won"
    assert body["is_won"] is True
    assert body["probability"] == 100
    assert body["closed_at"] is not None


async def test_lose_deal_closes_it(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Loser")

    create = await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={"title": "Lost cause", "contact_id": contact_id, "amount": 500_000},
    )
    deal_id = create.json()["id"]

    lose = await client.post(f"/api/v1/crm/deals/{deal_id}/lose", headers=headers)
    assert lose.status_code == 200
    assert lose.json()["status"] == "lost"
    assert lose.json()["probability"] == 0


async def test_filter_by_pipeline_and_status(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Filter Me")
    pipelines = (await client.get("/api/v1/crm/pipelines", headers=headers)).json()
    pipeline_id = pipelines[0]["id"]

    for title in ("Pipeline A", "Pipeline B", "Pipeline C"):
        await client.post(
            "/api/v1/crm/deals",
            headers=headers,
            json={"title": title, "contact_id": contact_id, "amount": 1000},
        )
    # Win one
    deals = (await client.get("/api/v1/crm/deals", headers=headers)).json()
    await client.post(f"/api/v1/crm/deals/{deals[0]['id']}/win", headers=headers)

    open_only = (await client.get("/api/v1/crm/deals?status=open", headers=headers)).json()
    assert len(open_only) == 2
    by_pipeline = (
        await client.get(f"/api/v1/crm/deals?pipeline_id={pipeline_id}", headers=headers)
    ).json()
    assert len(by_pipeline) == 3


async def test_forecast_weights_probability(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Forecast Lead")
    pipelines = (await client.get("/api/v1/crm/pipelines", headers=headers)).json()
    stages = pipelines[0]["stages"]
    proposal = next(s for s in stages if s["slug"] == "proposal")

    create = await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={"title": "F1", "contact_id": contact_id, "amount": 10_000_000},
    )
    await client.patch(
        f"/api/v1/crm/deals/{create.json()['id']}",
        headers=headers,
        json={"stage_id": proposal["id"]},
    )

    forecast = (await client.get("/api/v1/crm/deals/forecast", headers=headers)).json()
    assert forecast["open_count"] == 1
    assert forecast["open_amount"] == 10_000_000
    # 60% probability
    assert forecast["weighted_amount"] == 6_000_000


async def test_contact_deals_listing(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Multi-deal contact")
    for title in ("D1", "D2"):
        await client.post(
            "/api/v1/crm/deals",
            headers=headers,
            json={"title": title, "contact_id": contact_id, "amount": 100},
        )
    rows = (await client.get(f"/api/v1/crm/contacts/{contact_id}/deals", headers=headers)).json()
    assert len(rows) == 2


async def test_stats_reports_win_rate(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Stats Lead")
    for title in ("Won deal", "Lost deal", "Open deal"):
        d = await client.post(
            "/api/v1/crm/deals",
            headers=headers,
            json={"title": title, "contact_id": contact_id, "amount": 100},
        )
        if title == "Won deal":
            await client.post(f"/api/v1/crm/deals/{d.json()['id']}/win", headers=headers)
        elif title == "Lost deal":
            await client.post(f"/api/v1/crm/deals/{d.json()['id']}/lose", headers=headers)
    stats = (await client.get("/api/v1/crm/deals/stats", headers=headers)).json()
    assert stats["total"] == 3
    assert stats["by_status"].get("won") == 1
    assert stats["by_status"].get("lost") == 1
    assert stats["by_status"].get("open") == 1
    assert stats["win_rate"] == 0.5  # 1 won / 2 closed


async def test_delete_deal(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact_id = await _make_contact(client, headers, "Delete Me")
    create = await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={"title": "Soon gone", "contact_id": contact_id, "amount": 10},
    )
    deal_id = create.json()["id"]
    rm = await client.delete(f"/api/v1/crm/deals/{deal_id}", headers=headers)
    assert rm.status_code == 200
    rm2 = await client.delete(f"/api/v1/crm/deals/{deal_id}", headers=headers)
    assert rm2.status_code == 404
