"""Sprint 1.2 — Knowledge base ingest + RAG search."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services import knowledge_service
from app.services.sms import MockSMSProvider

# Force deterministic embeddings — no real OpenAI calls during tests.
os.environ["AI_MOCK"] = "true"
os.environ["EMBEDDINGS_MOCK"] = "true"
os.environ["META_MOCK"] = "true"

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
    resp = await client.post("/api/v1/brands", headers=headers, json={"name": name})
    return resp.json()["id"]


async def test_text_upload_creates_chunks(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")

    big_text = ("This is a knowledge document. " * 200).strip()
    resp = await client.post(
        "/api/v1/knowledge/documents/text",
        headers=headers,
        json={"brand_id": brand_id, "title": "Welcome guide", "text": big_text},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["embed_status"] == "ready"
    assert body["chunk_count"] >= 1
    assert body["title"] == "Welcome guide"
    assert body["section"] == "brand_overview"


async def test_sections_progress_tracks_eight_sections(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")

    for section, title in (
        ("products_services", "Services"),
        ("faq", "FAQ"),
    ):
        resp = await client.post(
            "/api/v1/knowledge/documents/text",
            headers=headers,
            json={
                "brand_id": brand_id,
                "section": section,
                "title": title,
                "text": f"{title} content for knowledge base.",
            },
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["section"] == section

    sections = (
        await client.get(f"/api/v1/knowledge/sections?brand_id={brand_id}", headers=headers)
    ).json()
    assert len(sections) == 8
    by_key = {section["key"]: section for section in sections}
    assert by_key["products_services"]["completed"] is True
    assert by_key["faq"]["completed"] is True
    assert by_key["brand_overview"]["completed"] is False

    stats = (
        await client.get(f"/api/v1/knowledge/stats?brand_id={brand_id}", headers=headers)
    ).json()
    assert stats["sections_total"] == 8
    assert stats["sections_completed"] == 2

    only_faq = (
        await client.get(
            f"/api/v1/knowledge/documents?brand_id={brand_id}&section=faq", headers=headers
        )
    ).json()
    assert len(only_faq) == 1
    assert only_faq[0]["title"] == "FAQ"


async def test_website_import_creates_section_document(
    client: AsyncClient, sample_register_payload: dict, monkeypatch: pytest.MonkeyPatch
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")

    async def fake_fetch(url: str) -> tuple[str, str | None]:
        assert url == "https://akme.example/"
        return "Akme salon services, working hours and booking policy.", "Akme home"

    monkeypatch.setattr(knowledge_service, "fetch_website_text", fake_fetch)

    resp = await client.post(
        "/api/v1/knowledge/import/website",
        headers=headers,
        json={
            "brand_id": brand_id,
            "section": "policies_processes",
            "url": "https://akme.example/",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source_type"] == "website"
    assert body["section"] == "policies_processes"
    assert body["title"] == "Akme home"


async def test_ai_chat_import_creates_document(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")

    resp = await client.post(
        "/api/v1/knowledge/import/ai-chat",
        headers=headers,
        json={
            "brand_id": brand_id,
            "section": "faq",
            "title": "AI FAQ",
            "prompt": "Salon har kuni 10:00 dan 22:00 gacha ishlaydi. Yozilish telefon orqali.",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source_type"] == "ai_chat"
    assert body["section"] == "faq"
    assert body["title"] == "AI FAQ"


async def test_instagram_import_uses_linked_account(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")

    linked = await client.post(
        "/api/v1/social/meta/link",
        headers=headers,
        json={
            "brand_id": brand_id,
            "page_id": "100000000000001",
            "target": "instagram",
        },
    )
    assert linked.status_code == 201, linked.text

    resp = await client.post(
        "/api/v1/knowledge/import/instagram",
        headers=headers,
        json={
            "brand_id": brand_id,
            "account_id": linked.json()["id"],
            "section": "social_proof",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source_type"] == "instagram"
    assert body["section"] == "social_proof"
    assert body["title"].startswith("Instagram @")


async def test_empty_text_returns_400(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    resp = await client.post(
        "/api/v1/knowledge/documents/text",
        headers=headers,
        json={"brand_id": brand_id, "title": "Empty", "text": "   "},
    )
    # Pydantic catches min_length OR our service raises 400
    assert resp.status_code in (400, 422)


async def test_list_documents_filtered_by_brand(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_a = await _make_brand(client, headers, "Brand A")
    brand_b = await _make_brand(client, headers, "Brand B")

    for brand_id in (brand_a, brand_b):
        await client.post(
            "/api/v1/knowledge/documents/text",
            headers=headers,
            json={"brand_id": brand_id, "title": f"Doc for {brand_id[:6]}", "text": "hello world"},
        )

    only_a = (
        await client.get(f"/api/v1/knowledge/documents?brand_id={brand_a}", headers=headers)
    ).json()
    only_b = (
        await client.get(f"/api/v1/knowledge/documents?brand_id={brand_b}", headers=headers)
    ).json()
    assert len(only_a) == 1
    assert len(only_b) == 1
    assert only_a[0]["brand_id"] == brand_a


async def test_delete_document(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    create = await client.post(
        "/api/v1/knowledge/documents/text",
        headers=headers,
        json={"brand_id": brand_id, "title": "Doc", "text": "Hello world from KB"},
    )
    doc_id = create.json()["id"]

    rm = await client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=headers)
    assert rm.status_code == 200

    rm2 = await client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=headers)
    assert rm2.status_code == 404


async def test_search_returns_top_k_with_similarity(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    docs = [
        ("Salons in Tashkent", "Beauty salon Akme is located in Tashkent center."),
        ("Pricing", "Manicure costs 100k, pedicure 150k."),
        ("Working hours", "Open daily from 10:00 to 22:00."),
    ]
    for title, text in docs:
        await client.post(
            "/api/v1/knowledge/documents/text",
            headers=headers,
            json={"brand_id": brand_id, "title": title, "text": text},
        )

    resp = await client.post(
        "/api/v1/knowledge/search",
        headers=headers,
        json={"query": "Manicure costs 100k, pedicure 150k.", "top_k": 3},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["query"]
    assert len(body["hits"]) > 0
    # Top hit must reference manicure / pedicure pricing (deterministic embeddings rank
    # exact-text closest to itself).
    top = body["hits"][0]
    assert top["similarity"] > 0.99
    assert "Manicure" in top["content"] or "pedicure" in top["content"].lower()


async def test_stats_reflects_document_count(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    initial = (await client.get("/api/v1/knowledge/stats", headers=headers)).json()
    assert initial["documents"] == 0
    assert initial["chunks"] == 0

    upload = await client.post(
        "/api/v1/knowledge/documents/text",
        headers=headers,
        json={"brand_id": brand_id, "title": "FAQ", "text": "First document. Second sentence."},
    )
    assert upload.status_code == 201, upload.text

    after = (await client.get("/api/v1/knowledge/stats", headers=headers)).json()
    assert after["documents"] == 1
    assert after["chunks"] >= 1
