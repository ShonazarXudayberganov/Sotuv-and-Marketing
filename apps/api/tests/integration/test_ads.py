"""Sprint 3.1 — Ad accounts, campaigns, metric snapshots, AI insights."""

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


async def _seed_full(client: AsyncClient, headers: dict) -> None:
    await client.post("/api/v1/ads/accounts/sync-mock", headers=headers)
    await client.post("/api/v1/ads/campaigns/sync-mock", headers=headers)
    await client.post("/api/v1/ads/snapshot", headers=headers)


async def test_sync_mock_accounts_creates_meta_and_google(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post("/api/v1/ads/accounts/sync-mock", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["inserted"] >= 4

    accounts = (await client.get("/api/v1/ads/accounts", headers=headers)).json()
    networks = {a["network"] for a in accounts}
    assert {"meta", "google"}.issubset(networks)


async def test_sync_mock_campaigns_creates_per_account(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post("/api/v1/ads/accounts/sync-mock", headers=headers)
    seed = await client.post("/api/v1/ads/campaigns/sync-mock", headers=headers)
    assert seed.status_code == 200, seed.text
    # 2 networks × 2 accounts × 3 campaigns = 12
    assert seed.json()["inserted"] == 12

    campaigns = (await client.get("/api/v1/ads/campaigns", headers=headers)).json()
    assert len(campaigns) == 12


async def test_create_draft_campaign(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post("/api/v1/ads/accounts/sync-mock", headers=headers)
    accounts = (await client.get("/api/v1/ads/accounts", headers=headers)).json()
    account_id = accounts[0]["id"]

    resp = await client.post(
        "/api/v1/ads/campaigns",
        headers=headers,
        json={
            "account_id": account_id,
            "name": "Bahor aksiyasi 2026",
            "objective": "leads",
            "daily_budget": 500_000,
            "currency": "UZS",
            "audience": {"age_min": 25, "age_max": 45, "interests": ["beauty"]},
            "creative": {"headline": "Yangi xizmat", "image_url": "https://x"},
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "draft"
    assert body["objective"] == "leads"
    assert body["daily_budget"] == 500_000
    assert body["audience"]["age_min"] == 25


async def test_create_draft_with_invalid_objective_400(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post("/api/v1/ads/accounts/sync-mock", headers=headers)
    accounts = (await client.get("/api/v1/ads/accounts", headers=headers)).json()

    resp = await client.post(
        "/api/v1/ads/campaigns",
        headers=headers,
        json={
            "account_id": accounts[0]["id"],
            "name": "Bad objective",
            "objective": "rocket-launch",
        },
    )
    assert resp.status_code == 400


async def test_metrics_snapshot_attaches_to_active_campaigns(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _seed_full(client, headers)

    campaigns = (await client.get("/api/v1/ads/campaigns", headers=headers)).json()
    # Active + paused (non-draft) campaigns get metrics
    with_metrics = [c for c in campaigns if c["metrics"] is not None]
    assert len(with_metrics) > 0
    sample = with_metrics[0]["metrics"]
    assert sample["impressions"] > 0
    assert sample["clicks"] > 0
    assert sample["spend"] > 0
    assert sample["ctr"] > 0  # basis points


async def test_overview_aggregates_kpis(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _seed_full(client, headers)

    overview = (await client.get("/api/v1/ads/overview", headers=headers)).json()
    assert overview["campaigns"] > 0
    assert overview["impressions"] > 0
    assert overview["clicks"] > 0
    assert overview["spend"] > 0
    assert "meta" in overview["by_network"]
    assert "google" in overview["by_network"]


async def test_filter_by_network(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _seed_full(client, headers)

    only_meta = (
        await client.get("/api/v1/ads/campaigns?network=meta", headers=headers)
    ).json()
    assert len(only_meta) > 0
    assert all(c["network"] == "meta" for c in only_meta)

    only_google = (
        await client.get("/api/v1/ads/overview?network=google", headers=headers)
    ).json()
    assert "google" in only_google["by_network"]
    assert "meta" not in only_google["by_network"]


async def test_update_campaign_changes_status(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post("/api/v1/ads/accounts/sync-mock", headers=headers)
    accounts = (await client.get("/api/v1/ads/accounts", headers=headers)).json()
    create = await client.post(
        "/api/v1/ads/campaigns",
        headers=headers,
        json={
            "account_id": accounts[0]["id"],
            "name": "To update",
            "objective": "traffic",
            "daily_budget": 100_000,
        },
    )
    cid = create.json()["id"]

    upd = await client.patch(
        f"/api/v1/ads/campaigns/{cid}",
        headers=headers,
        json={"status": "paused", "daily_budget": 200_000},
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "paused"
    assert upd.json()["daily_budget"] == 200_000


async def test_delete_campaign(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post("/api/v1/ads/accounts/sync-mock", headers=headers)
    accounts = (await client.get("/api/v1/ads/accounts", headers=headers)).json()
    create = await client.post(
        "/api/v1/ads/campaigns",
        headers=headers,
        json={
            "account_id": accounts[0]["id"],
            "name": "To delete",
            "objective": "traffic",
        },
    )
    cid = create.json()["id"]
    rm = await client.delete(f"/api/v1/ads/campaigns/{cid}", headers=headers)
    assert rm.status_code == 200
    rm2 = await client.delete(f"/api/v1/ads/campaigns/{cid}", headers=headers)
    assert rm2.status_code == 404


async def test_insights_returns_recommendations(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _seed_full(client, headers)

    resp = await client.get("/api/v1/ads/insights", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]
    assert isinstance(body["recommendations"], list)
    assert body["snapshot"]["campaigns"] > 0


async def test_insights_empty_state(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/ads/insights", headers=headers)
    body = resp.json()
    assert body["snapshot"]["campaigns"] == 0
    assert body["recommendations"] == []


async def test_timeseries_buckets_per_day(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await _seed_full(client, headers)

    rows = (
        await client.get("/api/v1/ads/timeseries?days=7", headers=headers)
    ).json()
    assert len(rows) >= 1
    assert rows[0]["impressions"] > 0
