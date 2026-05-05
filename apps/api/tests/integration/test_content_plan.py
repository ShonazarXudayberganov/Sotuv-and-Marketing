"""Content plan item CRUD, AI text import, and post conversion."""

from __future__ import annotations

import os
import re
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

os.environ["POST_WORKER_DISABLED"] = "true"
os.environ["TELEGRAM_MOCK"] = "true"

pytestmark = pytest.mark.asyncio


def _code_for(phone: str) -> str:
    for sent_phone, message in MockSMSProvider.sent:
        if sent_phone == phone:
            match = re.search(r"\b(\d{4,8})\b", message)
            if match:
                return match.group(1)
    raise AssertionError(f"No SMS sent to {phone}")


async def _bootstrap(client: AsyncClient, payload: dict) -> tuple[dict[str, str], str]:
    reg = await client.post("/api/v1/auth/register", json=payload)
    code = _code_for(payload["phone"])
    verify = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    bundle = verify.json()
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand = await client.post(
        "/api/v1/brands",
        headers=headers,
        json={"name": "Akme Beauty", "is_default": True},
    )
    return headers, brand.json()["id"]


async def _link_telegram(client: AsyncClient, headers: dict[str, str], brand_id: str) -> str:
    resp = await client.post(
        "/api/v1/social/telegram/link",
        headers=headers,
        json={"brand_id": brand_id, "chat": "@nexus_test"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_create_update_and_filter_content_plan_item(
    client: AsyncClient, sample_register_payload: dict
):
    headers, brand_id = await _bootstrap(client, sample_register_payload)
    planned_at = (datetime.now(UTC) + timedelta(days=3)).isoformat()

    create = await client.post(
        "/api/v1/content-plan",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "instagram",
            "title": "Before-after carousel",
            "idea": "Mijoz natijasini carousel formatida ko'rsatish.",
            "goal": "ishonch",
            "cta": "Konsultatsiyaga yoziling",
            "planned_at": planned_at,
        },
    )
    assert create.status_code == 201, create.text
    item = create.json()
    assert item["status"] == "idea"
    assert item["platform"] == "instagram"

    update = await client.patch(
        f"/api/v1/content-plan/{item['id']}",
        headers=headers,
        json={"status": "approved", "title": "Natija carousel"},
    )
    assert update.status_code == 200, update.text
    assert update.json()["status"] == "approved"
    assert update.json()["title"] == "Natija carousel"

    listing = await client.get(
        "/api/v1/content-plan",
        headers=headers,
        params={"brand_id": brand_id, "status": "approved"},
    )
    assert listing.status_code == 200
    assert [row["id"] for row in listing.json()] == [item["id"]]


async def test_import_ai_text_creates_dated_plan_items(
    client: AsyncClient, sample_register_payload: dict
):
    headers, brand_id = await _bootstrap(client, sample_register_payload)

    resp = await client.post(
        "/api/v1/content-plan/import-text",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "telegram",
            "topic": "May oyi aksiyalari",
            "start_date": date.today().isoformat(),
            "text": "\n".join(
                [
                    "Day 1: Aksiya haqida teaser post, CTA: yoziling",
                    "Day 2: Mijoz savollariga javob beruvchi post",
                    "Day 3: Natija va social proof",
                ]
            ),
        },
    )
    assert resp.status_code == 201, resp.text
    items = resp.json()["items"]
    assert len(items) == 3
    assert items[0]["source"] == "ai_import"
    assert items[0]["planned_at"] < items[1]["planned_at"] < items[2]["planned_at"]


async def test_create_post_from_content_plan_item(
    client: AsyncClient, sample_register_payload: dict
):
    headers, brand_id = await _bootstrap(client, sample_register_payload)
    account_id = await _link_telegram(client, headers, brand_id)

    create = await client.post(
        "/api/v1/content-plan",
        headers=headers,
        json={
            "brand_id": brand_id,
            "platform": "telegram",
            "title": "Aksiya e'loni",
            "idea": "Bugungi chegirma haqida qisqa Telegram posti.",
            "cta": "Bugun yoziling",
        },
    )
    item_id = create.json()["id"]
    scheduled_at = (datetime.now(UTC) + timedelta(hours=2)).isoformat()

    post = await client.post(
        f"/api/v1/content-plan/{item_id}/create-post",
        headers=headers,
        json={"social_account_ids": [account_id], "scheduled_at": scheduled_at},
    )
    assert post.status_code == 201, post.text
    body = post.json()
    assert body["status"] == "scheduled"
    assert body["title"] == "Aksiya e'loni"
    assert len(body["publications"]) == 1

    listing = await client.get(
        "/api/v1/content-plan", headers=headers, params={"brand_id": brand_id}
    )
    linked = next(row for row in listing.json() if row["id"] == item_id)
    assert linked["post_id"] == body["id"]
    assert linked["status"] == "scheduled"
