"""Sprint 3.2 — Reports/BI: cross-module overview, funnel, saved reports, export."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

os.environ["AI_MOCK"] = "true"
os.environ["ADS_MOCK"] = "true"

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


async def _seed(client: AsyncClient, headers: dict) -> None:
    """Populate every module so reports has real data."""
    # Contacts + deals
    contact = await client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={"full_name": "Akmal", "phone": "+998901112233", "status": "lead"},
    )
    cid = contact.json()["id"]
    await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={"title": "Birinchi bitim", "contact_id": cid, "amount": 5_000_000},
    )

    # Ads
    await client.post("/api/v1/ads/accounts/sync-mock", headers=headers)
    await client.post("/api/v1/ads/campaigns/sync-mock", headers=headers)
    await client.post("/api/v1/ads/snapshot", headers=headers)


async def test_overview_returns_all_module_blocks(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/reports/overview", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["period_days"] == 30
    assert "crm" in body
    assert "smm" in body
    assert "ads" in body
    assert "inbox" in body
    assert body["crm"]["contacts_total"] == 0


async def test_overview_reflects_seeded_data(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _seed(client, headers)
    body = (await client.get("/api/v1/reports/overview", headers=headers)).json()
    assert body["crm"]["contacts_total"] == 1
    assert body["crm"]["deals_open"] == 1
    assert body["ads"]["campaigns"] > 0


async def test_overview_rejects_bad_days(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/reports/overview?days=999", headers=headers)
    assert resp.status_code == 400


async def test_funnel_buckets_match_deal_probabilities(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    contact = await client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={"full_name": "Lead One", "status": "lead"},
    )
    cid = contact.json()["id"]
    pipelines = (await client.get("/api/v1/crm/pipelines", headers=headers)).json()
    proposal = next(s for s in pipelines[0]["stages"] if s["slug"] == "proposal")
    deal = await client.post(
        "/api/v1/crm/deals",
        headers=headers,
        json={"title": "Proposal stage", "contact_id": cid, "amount": 1_000_000},
    )
    await client.patch(
        f"/api/v1/crm/deals/{deal.json()['id']}",
        headers=headers,
        json={"stage_id": proposal["id"]},
    )

    body = (await client.get("/api/v1/reports/funnel", headers=headers)).json()
    assert body["deals"]["proposal"] == 1
    assert body["totals"]["deals"] == 1


async def test_cohorts_groups_by_month(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    for i in range(3):
        await client.post(
            "/api/v1/crm/contacts",
            headers=headers,
            json={
                "full_name": f"Contact {i}",
                "status": "customer" if i == 0 else "lead",
            },
        )
    rows = (await client.get("/api/v1/reports/cohorts?months=3", headers=headers)).json()
    assert len(rows) >= 1
    total_size = sum(r["size"] for r in rows)
    total_customers = sum(r["customers"] for r in rows)
    assert total_size == 3
    assert total_customers == 1


async def test_cohorts_rejects_bad_months(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    bad = await client.get("/api/v1/reports/cohorts?months=99", headers=headers)
    assert bad.status_code == 400


async def test_insights_returns_recommendations(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _seed(client, headers)
    resp = await client.get("/api/v1/reports/insights", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["summary"]
    assert isinstance(body["recommendations"], list)
    assert "snapshot" in body
    assert "funnel" in body


async def test_insights_empty_state(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    body = (await client.get("/api/v1/reports/insights", headers=headers)).json()
    # No CRM, SMM, or Ads data → empty-state summary
    assert "ma'lumot" in body["summary"].lower() or body["recommendations"] == []


async def test_saved_report_crud(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    create = await client.post(
        "/api/v1/reports/saved",
        headers=headers,
        json={
            "name": "Bosh sahifa",
            "description": "CRM + Ads",
            "definition": {
                "widgets": [
                    {"type": "kpi", "source": "crm.hot_leads"},
                    {"type": "timeseries", "source": "ads.spend", "days": 30},
                ]
            },
            "is_pinned": True,
        },
    )
    assert create.status_code == 201, create.text
    rid = create.json()["id"]
    assert create.json()["is_pinned"] is True

    listing = (await client.get("/api/v1/reports/saved", headers=headers)).json()
    assert any(r["id"] == rid for r in listing)

    upd = await client.patch(
        f"/api/v1/reports/saved/{rid}",
        headers=headers,
        json={"name": "Yangilangan nom", "is_pinned": False},
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Yangilangan nom"
    assert upd.json()["is_pinned"] is False

    rm = await client.delete(f"/api/v1/reports/saved/{rid}", headers=headers)
    assert rm.status_code == 200
    rm2 = await client.delete(f"/api/v1/reports/saved/{rid}", headers=headers)
    assert rm2.status_code == 404


async def test_export_contacts_csv(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={"full_name": "CSV User", "phone": "+998900000001", "status": "lead"},
    )
    resp = await client.get(
        "/api/v1/reports/export/contacts.csv", headers=headers
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    body = resp.text
    assert "full_name" in body
    assert "CSV User" in body


async def test_export_unknown_kind_returns_400(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get(
        "/api/v1/reports/export/unicorns.csv", headers=headers
    )
    assert resp.status_code == 400
