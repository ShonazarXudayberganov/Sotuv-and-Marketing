"""Sprint 1.4 — Meta (Facebook + Instagram) link & test publish."""

from __future__ import annotations

import os
import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

# Force deterministic Meta responses — no real Graph API calls during tests.
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


async def test_list_pages_returns_mock_pages(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/social/meta/pages", headers=headers)
    assert resp.status_code == 200, resp.text
    pages = resp.json()
    assert len(pages) >= 2
    assert pages[0]["has_instagram"] is True
    assert pages[0]["instagram_username"]


async def test_link_facebook_page_creates_account(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers, "Akme")
    pages = (await client.get("/api/v1/social/meta/pages", headers=headers)).json()
    page_id = pages[0]["id"]

    link = await client.post(
        "/api/v1/social/meta/link",
        headers=headers,
        json={"brand_id": brand_id, "page_id": page_id, "target": "facebook"},
    )
    assert link.status_code == 201, link.text
    body = link.json()
    assert body["provider"] == "facebook"
    assert body["external_id"] == page_id
    assert body["chat_type"] == "page"


async def test_link_instagram_uses_business_account_id(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    pages = (await client.get("/api/v1/social/meta/pages", headers=headers)).json()
    page_id = pages[0]["id"]

    link = await client.post(
        "/api/v1/social/meta/link",
        headers=headers,
        json={"brand_id": brand_id, "page_id": page_id, "target": "instagram"},
    )
    assert link.status_code == 201, link.text
    body = link.json()
    assert body["provider"] == "instagram"
    # IG external_id != FB page_id (mock generates a 178… id)
    assert body["external_id"] != page_id
    assert body["external_handle"]


async def test_link_unknown_page_returns_404(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)

    link = await client.post(
        "/api/v1/social/meta/link",
        headers=headers,
        json={"brand_id": brand_id, "page_id": "999999999999999", "target": "facebook"},
    )
    assert link.status_code == 404


async def test_test_publish_facebook_returns_post_id(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    pages = (await client.get("/api/v1/social/meta/pages", headers=headers)).json()
    link = await client.post(
        "/api/v1/social/meta/link",
        headers=headers,
        json={"brand_id": brand_id, "page_id": pages[0]["id"], "target": "facebook"},
    )
    account_id = link.json()["id"]

    send = await client.post(
        "/api/v1/social/meta/test",
        headers=headers,
        json={"account_id": account_id, "text": "Salom Facebook Page mock testdir."},
    )
    assert send.status_code == 200, send.text
    body = send.json()
    assert body["mocked"] is True
    assert body["target"] == "facebook"
    assert body["post_id"]


async def test_test_publish_instagram_requires_image_url(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    pages = (await client.get("/api/v1/social/meta/pages", headers=headers)).json()
    link = await client.post(
        "/api/v1/social/meta/link",
        headers=headers,
        json={"brand_id": brand_id, "page_id": pages[0]["id"], "target": "instagram"},
    )
    account_id = link.json()["id"]

    send_no_image = await client.post(
        "/api/v1/social/meta/test",
        headers=headers,
        json={"account_id": account_id, "text": "IG caption"},
    )
    assert send_no_image.status_code == 400

    send_ok = await client.post(
        "/api/v1/social/meta/test",
        headers=headers,
        json={
            "account_id": account_id,
            "text": "IG caption with image",
            "image_url": "https://example.com/image.jpg",
        },
    )
    assert send_ok.status_code == 200, send_ok.text
    assert send_ok.json()["target"] == "instagram"


async def test_test_publish_instagram_reels_requires_video_url(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    brand_id = await _make_brand(client, headers)
    pages = (await client.get("/api/v1/social/meta/pages", headers=headers)).json()
    link = await client.post(
        "/api/v1/social/meta/link",
        headers=headers,
        json={"brand_id": brand_id, "page_id": pages[0]["id"], "target": "instagram"},
    )
    account_id = link.json()["id"]

    send_bad = await client.post(
        "/api/v1/social/meta/test",
        headers=headers,
        json={
            "account_id": account_id,
            "text": "IG reels test",
            "content_format": "reels",
            "image_url": "https://example.com/cover.jpg",
        },
    )
    assert send_bad.status_code == 400

    send_ok = await client.post(
        "/api/v1/social/meta/test",
        headers=headers,
        json={
            "account_id": account_id,
            "text": "IG reels test",
            "content_format": "reels",
            "video_url": "https://example.com/reel.mp4",
        },
    )
    assert send_ok.status_code == 200, send_ok.text
    assert send_ok.json()["target"] == "instagram"


async def test_publish_instagram_post_builds_reels_payload(monkeypatch: pytest.MonkeyPatch):
    from app.services import meta_service

    monkeypatch.setenv("META_MOCK", "false")
    calls: list[dict[str, object]] = []

    async def fake_call(method: str, url: str, *, params=None, json_body=None):
        calls.append({"method": method, "url": url, "params": params, "json_body": json_body})
        return {"id": "creation-1"} if url.endswith("/media") else {"id": "publish-1"}

    monkeypatch.setattr(meta_service, "_call", fake_call)
    result = await meta_service.publish_instagram_post(
        None,  # type: ignore[arg-type]
        ig_user_id="178123",
        page_access_token="page-token",
        media_url="https://example.com/reel.mp4",
        caption="Reels caption",
        content_format="reels",
    )
    assert result["id"] == "publish-1"
    assert calls[0]["json_body"] == {
        "access_token": "page-token",
        "media_type": "REELS",
        "video_url": "https://example.com/reel.mp4",
        "caption": "Reels caption",
        "share_to_feed": True,
    }


async def test_publish_instagram_post_builds_story_payload(monkeypatch: pytest.MonkeyPatch):
    from app.services import meta_service

    monkeypatch.setenv("META_MOCK", "false")
    calls: list[dict[str, object]] = []

    async def fake_call(method: str, url: str, *, params=None, json_body=None):
        calls.append({"method": method, "url": url, "params": params, "json_body": json_body})
        return {"id": "creation-1"} if url.endswith("/media") else {"id": "publish-1"}

    monkeypatch.setattr(meta_service, "_call", fake_call)
    result = await meta_service.publish_instagram_post(
        None,  # type: ignore[arg-type]
        ig_user_id="178123",
        page_access_token="page-token",
        media_url="https://example.com/story.jpg",
        caption="Story caption",
        content_format="story",
    )
    assert result["id"] == "publish-1"
    assert calls[0]["json_body"] == {
        "access_token": "page-token",
        "media_type": "STORIES",
        "image_url": "https://example.com/story.jpg",
    }


async def test_publish_instagram_post_builds_feed_video_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.services import meta_service

    monkeypatch.setenv("META_MOCK", "false")
    calls: list[dict[str, object]] = []

    async def fake_call(method: str, url: str, *, params=None, json_body=None):
        calls.append({"method": method, "url": url, "params": params, "json_body": json_body})
        return {"id": "creation-1"} if url.endswith("/media") else {"id": "publish-1"}

    monkeypatch.setattr(meta_service, "_call", fake_call)
    result = await meta_service.publish_instagram_post(
        None,  # type: ignore[arg-type]
        ig_user_id="178123",
        page_access_token="page-token",
        media_url="https://example.com/feed.mp4",
        caption="Feed video",
        content_format="feed",
    )
    assert result["id"] == "publish-1"
    assert calls[0]["json_body"] == {
        "access_token": "page-token",
        "media_type": "VIDEO",
        "video_url": "https://example.com/feed.mp4",
        "caption": "Feed video",
    }


async def test_test_publish_unknown_account_returns_404(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    fake_id = "00000000-0000-0000-0000-000000000000"
    send = await client.post(
        "/api/v1/social/meta/test",
        headers=headers,
        json={"account_id": fake_id, "text": "hi"},
    )
    assert send.status_code == 404
