"""Meta Graph API client — Facebook Pages + Instagram Business.

Uses the tenant's Meta credentials from ``tenant_integrations`` (provider="meta_app").
Required credential fields: ``app_id`` and ``app_secret``.
OAuth grants store ``user_access_token`` and page selections keep page tokens in
linked social account metadata.

When ``META_MOCK=true`` or no creds are configured, returns deterministic mock
responses so the rest of the pipeline keeps working in tests/dev.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.integration_service import get_credentials

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
GRAPH_DIALOG_BASE = "https://www.facebook.com/v21.0/dialog/oauth"
TIMEOUT_SECONDS = 20
META_OAUTH_SCOPES = (
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_posts",
    "instagram_basic",
    "instagram_content_publish",
)


class MetaError(RuntimeError):
    """Raised when the Meta Graph API returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        subcode: int | None = None,
        error_type: str | None = None,
        is_transient: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.subcode = subcode
        self.error_type = error_type
        self.is_transient = is_transient or code in {1, 2, 4, 17, 32, 613}

    @property
    def is_auth(self) -> bool:
        return self.code in {10, 102, 190, 200} or self.error_type == "OAuthException"


def _is_mock_mode() -> bool:
    return os.getenv("META_MOCK", "false").lower() in {"1", "true", "yes"}


async def _credentials(db: AsyncSession) -> dict[str, Any] | None:
    return await get_credentials(db, "meta_app")


def _require_app_credentials(creds: dict[str, Any] | None) -> tuple[str, str]:
    app_id = str((creds or {}).get("app_id") or "").strip()
    app_secret = str((creds or {}).get("app_secret") or "").strip()
    if not app_id or not app_secret:
        raise MetaError("Meta app_id va app_secret avval integratsiyalarda kiritilishi kerak")
    return app_id, app_secret


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
        if isinstance(err, dict):
            msg = err.get("message") or f"Meta API error (status={resp.status_code})"
            code = err.get("code")
            subcode = err.get("error_subcode")
            raise MetaError(
                str(msg),
                code=int(code) if isinstance(code, int) else None,
                subcode=int(subcode) if isinstance(subcode, int) else None,
                error_type=str(err.get("type")) if err.get("type") else None,
                is_transient=bool(err.get("is_transient") or False),
            )
        raise MetaError(f"Meta API error (status={resp.status_code})")
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


def _mock_authorize_url(redirect_uri: str, state: str) -> str:
    return f"{redirect_uri}?code=mock-meta-code&state={state}"


def _mock_instagram_snapshot(ig_user_id: str) -> dict[str, Any]:
    username = f"akme_{ig_user_id[-3:]}"
    return {
        "id": ig_user_id,
        "username": username,
        "name": "Mock IG Business",
        "biography": "Toshkentdagi zamonaviy beauty xizmatlari. Har kuni 10:00-22:00.",
        "followers_count": 12840,
        "media_count": 186,
        "media": {
            "data": [
                {
                    "caption": (
                        "Yangi manikyur kolleksiyasi: nozik ranglar va uzoq saqlanuvchi " "qoplama."
                    ),
                    "media_type": "IMAGE",
                    "permalink": f"https://instagram.com/{username}/p/mock1",
                    "timestamp": "2026-04-15T10:00:00+0000",
                    "like_count": 342,
                    "comments_count": 18,
                },
                {
                    "caption": "Bahor aksiyasi: pedikyur + SPA parvarish paketiga chegirma.",
                    "media_type": "REELS",
                    "permalink": f"https://instagram.com/{username}/p/mock2",
                    "timestamp": "2026-04-20T14:30:00+0000",
                    "like_count": 518,
                    "comments_count": 31,
                },
            ]
        },
    }


# ─────────── Public API ───────────


async def list_pages(db: AsyncSession) -> list[dict[str, Any]]:
    """List Facebook Pages this app has been granted access to."""
    if _is_mock_mode():
        return _mock_pages()
    creds = await _credentials(db)
    token = (creds or {}).get("page_access_token") or (creds or {}).get("user_access_token")
    if not token:
        raise MetaError("Meta OAuth hali yakunlanmagan. Avval integratsiyalarda ruxsat bering")
    data = await _list_pages_by_token(str(token))
    pages = data.get("data")
    if not isinstance(pages, list):
        raise MetaError("Unexpected /me/accounts response shape")
    return pages


async def _list_pages_by_token(access_token: str) -> dict[str, Any]:
    return await _call(
        "GET",
        f"{GRAPH_API_BASE}/me/accounts",
        params={"access_token": access_token, "fields": "id,name,access_token,category,tasks"},
    )


async def build_oauth_authorize_url(
    db: AsyncSession,
    *,
    redirect_uri: str,
    state: str,
) -> str:
    """Construct the Meta Login URL for this tenant's configured app."""
    if _is_mock_mode():
        return _mock_authorize_url(redirect_uri, state)
    creds = await _credentials(db)
    app_id, _ = _require_app_credentials(creds)
    query = urlencode(
        {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": ",".join(META_OAUTH_SCOPES),
            "response_type": "code",
        }
    )
    return f"{GRAPH_DIALOG_BASE}?{query}"


async def exchange_oauth_code(
    db: AsyncSession,
    *,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    """Exchange a Meta OAuth code for a long-lived user token and page snapshot."""
    if _is_mock_mode():
        mock_pages = _mock_pages()
        return {
            "user_access_token": f"mock_user_token_{abs(hash(code)) % 1_000_000}",
            "page_access_token": mock_pages[0]["access_token"],
            "page_name": mock_pages[0]["name"],
            "pages_count": len(mock_pages),
        }
    creds = await _credentials(db)
    app_id, app_secret = _require_app_credentials(creds)
    short_lived = await _call(
        "GET",
        f"{GRAPH_API_BASE}/oauth/access_token",
        params={
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
    )
    short_token = str(short_lived.get("access_token") or "")
    if not short_token:
        raise MetaError("Meta OAuth code exchange access_token qaytarmadi")
    exchange = await _call(
        "GET",
        f"{GRAPH_API_BASE}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token,
        },
    )
    long_lived_token = str(exchange.get("access_token") or short_token)
    page_data = await _list_pages_by_token(long_lived_token)
    raw_pages = page_data.get("data")
    if not isinstance(raw_pages, list):
        raise MetaError("Unexpected /me/accounts response shape")
    pages: list[dict[str, Any]] = [page for page in raw_pages if isinstance(page, dict)]
    first_page = next((page for page in pages if isinstance(page, dict)), None)
    return {
        "user_access_token": long_lived_token,
        "page_access_token": str((first_page or {}).get("access_token") or "") or None,
        "page_name": str((first_page or {}).get("name") or "") or None,
        "pages_count": len(pages),
    }


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


async def refresh_page_token(db: AsyncSession, *, page_id: str) -> str | None:
    """Refresh/re-resolve a Page token from a stored user token when available."""
    if _is_mock_mode():
        return f"mock_refreshed_page_token_{page_id[-6:]}"
    creds = await _credentials(db)
    if not creds:
        return None
    app_id, app_secret = _require_app_credentials(creds)
    user_token = creds.get("user_access_token")
    if not user_token:
        return None

    exchange = await _call(
        "GET",
        f"{GRAPH_API_BASE}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": str(user_token),
        },
    )
    long_lived_user_token = str(exchange.get("access_token") or user_token)
    pages = await _call(
        "GET",
        f"{GRAPH_API_BASE}/me/accounts",
        params={
            "access_token": long_lived_user_token,
            "fields": "id,name,access_token",
        },
    )
    for page in pages.get("data") or []:
        if isinstance(page, dict) and str(page.get("id")) == page_id:
            token = page.get("access_token")
            return str(token) if token else None
    return None


async def get_published_object(
    db: AsyncSession,
    *,
    object_id: str,
    access_token: str,
) -> dict[str, Any]:
    """Read back a published Meta object to verify it is still live/reachable."""
    if _is_mock_mode():
        return {
            "id": object_id,
            "status": "live",
            "permalink_url": f"https://facebook.com/{object_id}",
        }
    return await _call(
        "GET",
        f"{GRAPH_API_BASE}/{object_id}",
        params={
            "access_token": access_token,
            "fields": "id,permalink_url",
        },
    )


async def get_instagram_profile_snapshot(
    db: AsyncSession,
    *,
    ig_user_id: str,
    page_token: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    """Fetch profile + recent media captions for KB import."""
    if _is_mock_mode():
        return _mock_instagram_snapshot(ig_user_id)
    creds = await _credentials(db)
    token = page_token or (creds or {}).get("page_access_token")
    if not token:
        raise MetaError("Instagram import uchun page token topilmadi")
    fields = (
        "id,username,name,biography,followers_count,media_count,"
        f"media.limit({limit})"
        "{caption,media_type,permalink,timestamp,like_count,comments_count}"
    )
    return await _call(
        "GET",
        f"{GRAPH_API_BASE}/{ig_user_id}",
        params={"access_token": str(token), "fields": fields},
    )


__all__ = [
    "META_OAUTH_SCOPES",
    "MetaError",
    "build_oauth_authorize_url",
    "exchange_oauth_code",
    "get_instagram_business_account",
    "get_instagram_profile_snapshot",
    "get_published_object",
    "list_pages",
    "publish_facebook_post",
    "publish_instagram_post",
    "refresh_page_token",
]
