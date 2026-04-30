"""Meta Graph API client — Facebook Pages + Instagram Business.

Uses the tenant's Meta credentials from ``tenant_integrations`` (provider="meta_app").
Required credential fields: ``app_id``, ``app_secret``, ``page_access_token``.
The page access token is long-lived and grants posting rights on managed pages.

When ``META_MOCK=true`` or no creds are configured, returns deterministic mock
responses so the rest of the pipeline keeps working in tests/dev.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.integration_service import get_credentials

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
TIMEOUT_SECONDS = 20


class MetaError(RuntimeError):
    """Raised when the Meta Graph API returns an error response."""


def _is_mock_mode() -> bool:
    return os.getenv("META_MOCK", "false").lower() in {"1", "true", "yes"}


async def _credentials(db: AsyncSession) -> dict[str, Any] | None:
    return await get_credentials(db, "meta_app")


async def _call(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
        resp = await http.request(method, url, params=params, json=json_body)
        try:
            raw = resp.json()
        except ValueError as exc:
            raise MetaError(f"Non-JSON response (status={resp.status_code})") from exc
    if not isinstance(raw, dict):
        raise MetaError("Unexpected non-object response")
    data: dict[str, Any] = raw
    if resp.status_code >= 400 or "error" in data:
        err = data.get("error") or {}
        msg = (err.get("message") if isinstance(err, dict) else None) or (
            f"Meta API error (status={resp.status_code})"
        )
        raise MetaError(str(msg))
    return data


# ─────────── Mock helpers ───────────


def _mock_pages() -> list[dict[str, Any]]:
    return [
        {
            "id": "100000000000001",
            "name": "Mock Akme Page",
            "access_token": "mock_page_token",
            "category": "Business",
            "tasks": ["CREATE_CONTENT", "MANAGE", "MODERATE"],
        },
        {
            "id": "100000000000002",
            "name": "Mock Pro Studio",
            "access_token": "mock_page_token_2",
            "category": "Marketing Agency",
            "tasks": ["CREATE_CONTENT", "MANAGE"],
        },
    ]


def _mock_ig_account(page_id: str) -> dict[str, Any] | None:
    return {
        "id": f"178{page_id[-6:]}",
        "username": f"akme_{page_id[-3:]}",
        "name": "Mock IG Business",
    }


def _mock_publish(text: str) -> dict[str, Any]:
    return {"id": f"mock_post_{abs(hash(text)) % 1_000_000}"}


# ─────────── Public API ───────────


async def list_pages(db: AsyncSession) -> list[dict[str, Any]]:
    """List Facebook Pages this app has been granted access to."""
    if _is_mock_mode():
        return _mock_pages()
    creds = await _credentials(db)
    token = (creds or {}).get("page_access_token") or (creds or {}).get("user_access_token")
    if not token:
        raise MetaError("Meta credentials are not configured")
    data = await _call(
        "GET",
        f"{GRAPH_API_BASE}/me/accounts",
        params={"access_token": str(token), "fields": "id,name,access_token,category,tasks"},
    )
    pages = data.get("data")
    if not isinstance(pages, list):
        raise MetaError("Unexpected /me/accounts response shape")
    return pages


async def get_instagram_business_account(
    db: AsyncSession, *, page_id: str, page_token: str | None = None
) -> dict[str, Any] | None:
    """Resolve the IG Business account linked to a Facebook Page (if any)."""
    if _is_mock_mode():
        return _mock_ig_account(page_id)
    creds = await _credentials(db)
    token = page_token or (creds or {}).get("page_access_token")
    if not token:
        raise MetaError("Meta credentials are not configured")
    data = await _call(
        "GET",
        f"{GRAPH_API_BASE}/{page_id}",
        params={"access_token": str(token), "fields": "instagram_business_account"},
    )
    ig_ref = data.get("instagram_business_account")
    if not ig_ref:
        return None
    ig_id = ig_ref.get("id")
    if not ig_id:
        return None
    profile = await _call(
        "GET",
        f"{GRAPH_API_BASE}/{ig_id}",
        params={"access_token": str(token), "fields": "id,username,name"},
    )
    return profile


async def publish_facebook_post(
    db: AsyncSession,
    *,
    page_id: str,
    page_access_token: str,
    message: str,
    link: str | None = None,
) -> dict[str, Any]:
    """Publish a text/link post to a Facebook Page feed."""
    if _is_mock_mode():
        return _mock_publish(message)
    payload: dict[str, Any] = {"message": message, "access_token": page_access_token}
    if link:
        payload["link"] = link
    return await _call("POST", f"{GRAPH_API_BASE}/{page_id}/feed", json_body=payload)


async def publish_instagram_post(
    db: AsyncSession,
    *,
    ig_user_id: str,
    page_access_token: str,
    image_url: str,
    caption: str,
) -> dict[str, Any]:
    """Two-step IG publish: create container, then publish it."""
    if _is_mock_mode():
        return _mock_publish(caption)
    container = await _call(
        "POST",
        f"{GRAPH_API_BASE}/{ig_user_id}/media",
        json_body={
            "image_url": image_url,
            "caption": caption,
            "access_token": page_access_token,
        },
    )
    creation_id = container.get("id")
    if not creation_id:
        raise MetaError("Instagram container creation failed")
    return await _call(
        "POST",
        f"{GRAPH_API_BASE}/{ig_user_id}/media_publish",
        json_body={"creation_id": creation_id, "access_token": page_access_token},
    )


__all__ = [
    "MetaError",
    "get_instagram_business_account",
    "list_pages",
    "publish_facebook_post",
    "publish_instagram_post",
]
