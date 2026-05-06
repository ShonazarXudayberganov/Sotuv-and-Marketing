"""Sprint 1.9 — SMM analytics: overview, timeseries, top posts, optimal times, AI insights."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

# Disable worker; mock providers + AI keep the suite deterministic.
os.environ["POST_WORKER_DISABLED"] = "true"
os.environ["TELEGRAM_MOCK"] = "true"
os.environ["META_MOCK"] = "true"
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


async def _seed_published_post(client: AsyncClient, headers: dict, brand_id: str, body: str) -> str:
    """Create a Telegram-linked post and publish it now."""
    link = await client.post(
        "/api/v1/social/telegram/link",
        headers=headers,
        json={"brand_id": brand_id, "chat": f"@chan_{abs(hash(body)) % 10_000}"},
    )
    account_id = link.json()["id"]
    create = await client.post(
        "/api/v1/posts",
        headers=headers,
        json={
            "brand_id": brand_id,
            "body": body,
            "social_account_ids": [account_id],
        },
    )
    post_id = create.json()["id"]
    await client.post(f"/api/v1/posts/{post_id}/publish-now", headers=headers)
    return post_id


async def _make_brand(client: AsyncClient, headers: dict) -> str:
    resp = await client.post("/api/v1/brands", headers=headers, json={"name": "Akme"})
    return resp.json()["id"]


async def _link_instagram(client: AsyncClient, headers: dict, brand_id: str) -> str:
    pages = (await client.get("/api/v1/social/meta/pages", headers=headers)).json()
    resp = await client.post(
        "/api/v1/social/meta/link",
        headers=headers,
        json={"brand_id": brand_id, "page_id": pages[0]["id"], "target": "instagram"},
    )
    return resp.json()["id"]


async def test_overview_zero_when_no_metrics(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/analytics/overview", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_posts"] == 0
    assert body["engagement_rate"] == 0.0
    assert body["by_platform"] == {}


async def test_snapshot_then_overview_aggregates(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    for body in ("Yangi xizmat e'loni", "Bahor aksiyasi", "FAQ — ish vaqti"):
        await _seed_published_post(client, headers, brand_id, body)

    snap = await client.post("/api/v1/analytics/snapshot", headers=headers)
    assert snap.status_code == 200
    assert snap.json()["inserted"] == 3

    overview = (await client.get("/api/v1/analytics/overview", headers=headers)).json()
    assert overview["total_posts"] == 3
    assert overview["total_views"] > 0
    assert overview["engagement_rate"] > 0
    assert "telegram" in overview["by_platform"]
    assert overview["by_platform"]["telegram"]["posts"] == 3


async def test_top_posts_sorted_by_engagement(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    for body in ("a", "b", "c", "d", "e"):
        await _seed_published_post(client, headers, brand_id, f"post-{body}")
    await client.post("/api/v1/analytics/snapshot", headers=headers)

    top = (await client.get("/api/v1/analytics/top-posts?limit=3", headers=headers)).json()
    assert len(top) == 3
    engagements = [t["engagement"] for t in top]
    assert engagements == sorted(engagements, reverse=True)


async def test_timeseries_returns_per_day_buckets(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    for body in ("p1", "p2"):
        await _seed_published_post(client, headers, brand_id, body)
    await client.post("/api/v1/analytics/snapshot", headers=headers)

    rows = (await client.get("/api/v1/analytics/timeseries?days=30", headers=headers)).json()
    assert len(rows) >= 1
    # Posts published today should land in a single bucket
    assert sum(r["posts"] for r in rows) >= 2


async def test_snapshot_prefers_meta_metrics_when_available(
    client: AsyncClient,
    sample_register_payload: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.services import meta_service

    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    account_id = await _link_instagram(client, headers, brand_id)

    create = await client.post(
        "/api/v1/posts",
        headers=headers,
        json={
            "brand_id": brand_id,
            "body": "Instagram analytics test",
            "content_format": "feed",
            "media_urls": ["https://example.com/feed.jpg"],
            "social_account_ids": [account_id],
        },
    )
    post_id = create.json()["id"]
    await client.post(f"/api/v1/posts/{post_id}/publish-now", headers=headers)

    async def fake_metrics(db, *, provider: str, object_id: str, access_token: str):
        assert provider == "instagram"
        assert object_id
        assert access_token
        return {"likes": 77, "comments": 9, "shares": 0}

    async def fake_insights(
        db,
        *,
        provider: str,
        object_id: str,
        access_token: str,
        content_format: str,
    ):
        assert provider == "instagram"
        assert content_format == "feed"
        return {"views": 1234, "reach": 987}

    monkeypatch.setattr(meta_service, "get_post_metrics", fake_metrics)
    monkeypatch.setattr(meta_service, "get_post_insights", fake_insights)

    snap = await client.post("/api/v1/analytics/snapshot", headers=headers)
    assert snap.status_code == 200, snap.text

    overview = (await client.get("/api/v1/analytics/overview", headers=headers)).json()
    assert overview["total_posts"] == 1
    assert overview["total_views"] == 1234
    assert overview["total_likes"] == 77
    assert overview["total_comments"] == 9


async def test_timeseries_rejects_bad_days(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    bad = await client.get("/api/v1/analytics/timeseries?days=500", headers=headers)
    assert bad.status_code == 400


async def test_optimal_times_picks_best_cells(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    for body in ("o1", "o2", "o3"):
        await _seed_published_post(client, headers, brand_id, body)
    await client.post("/api/v1/analytics/snapshot", headers=headers)

    resp = await client.get("/api/v1/analytics/optimal-times", headers=headers)
    body = resp.json()
    assert resp.status_code == 200
    assert isinstance(body["cells"], list)
    assert len(body["best"]) <= 3
    if body["best"]:
        assert 0 <= body["best"][0]["weekday"] <= 6
        assert 0 <= body["best"][0]["hour"] <= 23


async def test_insights_returns_summary_and_recommendations(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    for body in ("i1", "i2", "i3"):
        await _seed_published_post(client, headers, brand_id, body)
    await client.post("/api/v1/analytics/snapshot", headers=headers)

    resp = await client.get("/api/v1/analytics/insights", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["summary"]
    assert isinstance(body["recommendations"], list)
    assert body["snapshot"]["total_posts"] == 3
    assert "top_posts" in body
    assert "optimal" in body


async def test_insights_empty_state(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/analytics/insights", headers=headers)
    body = resp.json()
    assert body["snapshot"]["total_posts"] == 0
    assert body["recommendations"] == []
