"""Sprint 1.2 — Knowledge base ingest + RAG search."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

# Force deterministic embeddings — no real OpenAI calls during tests.
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
