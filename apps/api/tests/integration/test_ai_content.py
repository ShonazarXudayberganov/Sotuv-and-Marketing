"""Sprint 1.6 — AI content generation pipeline."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

# Force deterministic AI + RAG — no real provider calls.
os.environ["AI_MOCK"] = "true"
os.environ["EMBEDDINGS_MOCK"] = "true"

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
    resp = await client.post(
        "/api/v1/brands",
        headers=headers,
        json={
            "name": name,
            "industry": "salon-klinika",
            "voice_tone": "Iliq, professional",
            "target_audience": "25-45 yosh ayollar",
        },
    )
    return resp.json()["id"]


async def test_generate_post_creates_draft_with_mock_provider(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")

    resp = await client.post(
        "/api/v1/ai/generate-post",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "telegram",
            "user_goal": "E'lon: yangi xizmat haftalik chegirma bilan.",
            "language": "uz",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["platform"] == "telegram"
    assert body["body"]
    assert body["tokens_used"] > 0


async def test_generate_post_caches_identical_request(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    payload = {
        "brand_id": brand_id,
        "platform": "instagram",
        "user_goal": "Manikur uchun pre-launch e'lon.",
        "language": "uz",
    }
    first = await client.post("/api/v1/ai/generate-post", headers=headers, json=payload)
    second = await client.post("/api/v1/ai/generate-post", headers=headers, json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    # Cache hit reuses the same draft id
    assert first.json()["id"] == second.json()["id"]


async def test_generate_content_creates_three_variants(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    resp = await client.post(
        "/api/v1/ai/generate-content",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "instagram",
            "user_goal": "Yangi xizmat uchun launch posti.",
            "language": "uz",
            "variants": 3,
            "use_cache": False,
        },
    )

    assert resp.status_code == 201, resp.text
    drafts = resp.json()["drafts"]
    assert len(drafts) == 3
    assert [d["title"].split(" - ")[-1] for d in drafts] == [
        "Variant A",
        "Variant B",
        "Variant C",
    ]
    assert {d["provider"] for d in drafts} == {"mock"}


async def test_list_drafts_filters_by_brand_and_platform(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_a = await _make_brand(client, headers, "Brand A")
    brand_b = await _make_brand(client, headers, "Brand B")

    for brand_id, platform in (
        (brand_a, "telegram"),
        (brand_a, "instagram"),
        (brand_b, "telegram"),
    ):
        await client.post(
            "/api/v1/ai/generate-post",
            headers=headers,
            json={
                "brand_id": brand_id,
                "platform": platform,
                "user_goal": f"hello {brand_id[:6]} {platform}",
                "language": "uz",
            },
        )

    only_a = (await client.get(f"/api/v1/ai/drafts?brand_id={brand_a}", headers=headers)).json()
    only_a_telegram = (
        await client.get(f"/api/v1/ai/drafts?brand_id={brand_a}&platform=telegram", headers=headers)
    ).json()
    assert len(only_a) == 2
    assert len(only_a_telegram) == 1
    assert only_a_telegram[0]["platform"] == "telegram"


async def test_star_and_unstar_draft(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    create = await client.post(
        "/api/v1/ai/generate-post",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "facebook",
            "user_goal": "Yangi mijozlarga chegirma haqida",
            "language": "uz",
        },
    )
    draft_id = create.json()["id"]
    assert create.json()["is_starred"] is False

    star = await client.post(f"/api/v1/ai/drafts/{draft_id}/star", headers=headers)
    assert star.status_code == 200
    assert star.json()["is_starred"] is True

    unstar = await client.post(f"/api/v1/ai/drafts/{draft_id}/star", headers=headers)
    assert unstar.json()["is_starred"] is False


async def test_update_draft_invalidates_cache(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    payload = {
        "brand_id": brand_id,
        "platform": "telegram",
        "user_goal": "Salondagi yangi xizmat e'loni.",
        "language": "uz",
    }
    create = await client.post("/api/v1/ai/generate-post", headers=headers, json=payload)
    draft_id = create.json()["id"]

    edit = await client.patch(
        f"/api/v1/ai/drafts/{draft_id}",
        headers=headers,
        json={"body": "Tahrirlangan post matni"},
    )
    assert edit.status_code == 200
    assert edit.json()["body"] == "Tahrirlangan post matni"

    # Cache invalidated -> regeneration creates a NEW draft, not the same id
    again = await client.post("/api/v1/ai/generate-post", headers=headers, json=payload)
    assert again.json()["id"] != draft_id


async def test_improve_content_updates_draft(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    create = await client.post(
        "/api/v1/ai/generate-post",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "telegram",
            "user_goal": "Yangi xizmat e'loni.",
            "language": "uz",
        },
    )
    draft = create.json()
    improve = await client.post(
        "/api/v1/ai/improve-content",
        headers=headers,
        json={"draft_id": draft["id"], "instruction": "Qisqartir va CTA ni kuchaytir"},
    )

    assert improve.status_code == 200, improve.text
    assert improve.json()["id"] == draft["id"]
    assert improve.json()["body"] != draft["body"]
    assert improve.json()["tokens_used"] > draft["tokens_used"]


async def test_delete_draft(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    create = await client.post(
        "/api/v1/ai/generate-post",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "telegram",
            "user_goal": "Eski xizmat haqida",
            "language": "uz",
        },
    )
    draft_id = create.json()["id"]

    rm = await client.delete(f"/api/v1/ai/drafts/{draft_id}", headers=headers)
    assert rm.status_code == 200
    rm2 = await client.delete(f"/api/v1/ai/drafts/{draft_id}", headers=headers)
    assert rm2.status_code == 404


async def test_usage_increments_after_generation(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    before = (await client.get("/api/v1/ai/usage", headers=headers)).json()
    assert before["tokens_used"] == 0

    await client.post(
        "/api/v1/ai/generate-post",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "telegram",
            "user_goal": "Birinchi avtomatik post.",
            "language": "uz",
        },
    )
    after = (await client.get("/api/v1/ai/usage", headers=headers)).json()
    assert after["tokens_used"] > before["tokens_used"]
    assert after["period"] == before["period"]


async def test_ai_chat_returns_brand_scoped_answer(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Chat Brand")

    resp = await client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={
            "brand_id": brand_id,
            "message": "Ushbu brend uchun post hook taklif qil",
            "language": "uz",
            "history": [{"role": "user", "content": "Sotuvga urg'u beramiz"}],
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["text"]
    assert body["tokens_used"] > 0


async def test_hashtags_reels_and_plan_generators(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Plan Brand")

    hashtags = await client.post(
        "/api/v1/ai/generate-hashtags",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "instagram",
            "topic": "Bahor aksiyasi",
            "language": "uz",
            "count": 12,
        },
    )
    assert hashtags.status_code == 200, hashtags.text
    tags = hashtags.json()["hashtags"]
    assert 1 <= len(tags) <= 12
    assert all(tag.startswith("#") for tag in tags)

    reels = await client.post(
        "/api/v1/ai/generate-reels-script",
        headers=headers,
        json={
            "brand_id": brand_id,
            "topic": "Yangi xizmatni Reels orqali tanishtirish",
            "language": "uz",
            "duration_seconds": 30,
        },
    )
    assert reels.status_code == 200, reels.text
    assert reels.json()["text"]

    plan = await client.post(
        "/api/v1/ai/generate-30-day-plan",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "instagram",
            "topic": "Bahor kampaniyasi",
            "language": "uz",
            "days": 30,
        },
    )
    assert plan.status_code == 200, plan.text
    assert plan.json()["tokens_used"] > 0


async def test_stats_reflects_drafts_by_platform(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    for platform in ("telegram", "instagram", "telegram"):
        await client.post(
            "/api/v1/ai/generate-post",
            headers=headers,
            json={
                "brand_id": brand_id,
                "platform": platform,
                "user_goal": f"goal-{platform}-{abs(hash(platform))}",
                "language": "uz",
            },
        )
    stats = (await client.get("/api/v1/ai/stats", headers=headers)).json()
    # 2 unique cache keys for telegram (different goals), 1 for instagram
    assert stats["drafts_total"] >= 2
    assert "telegram" in stats["by_platform"]
