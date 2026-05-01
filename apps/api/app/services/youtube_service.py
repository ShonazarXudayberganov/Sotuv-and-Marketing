"""YouTube Data API v3 client.

For Sprint 1.5 we cover read operations only (channel info, recent videos,
aggregate stats). Uploads need an OAuth refresh token + resumable upload
protocol — that's wired in a later sprint.

Credentials live in ``tenant_integrations`` (provider="youtube"). Required:
  - ``api_key`` for public read endpoints (channels.list, search, videos.list)
  - ``oauth_refresh_token`` (optional now, used for uploads later)

When ``YOUTUBE_MOCK=true`` or no creds are configured, returns deterministic
mock responses so the rest of the pipeline keeps working in tests/dev.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.integration_service import get_credentials

logger = logging.getLogger(__name__)

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
TIMEOUT_SECONDS = 20


class YouTubeError(RuntimeError):
    """Raised when the YouTube API returns an error response."""


def _is_mock_mode() -> bool:
    return os.getenv("YOUTUBE_MOCK", "false").lower() in {"1", "true", "yes"}


async def _api_key(db: AsyncSession) -> str | None:
    creds = await get_credentials(db, "youtube")
    if not creds:
        return None
    key = creds.get("api_key")
    return str(key) if key else None


async def _call(path: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"{YOUTUBE_API}/{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
        resp = await http.get(url, params=params)
        try:
            raw = resp.json()
        except ValueError as exc:
            raise YouTubeError(f"Non-JSON response (status={resp.status_code})") from exc
    if not isinstance(raw, dict):
        raise YouTubeError("Unexpected non-object response")
    data: dict[str, Any] = raw
    if resp.status_code >= 400 or "error" in data:
        err = data.get("error") or {}
        msg = (err.get("message") if isinstance(err, dict) else None) or (
            f"YouTube API error (status={resp.status_code})"
        )
        raise YouTubeError(str(msg))
    return data


# ─────────── Mock helpers ───────────


def _mock_channel(handle: str) -> dict[str, Any]:
    base = handle.lstrip("@") or "channel"
    return {
        "id": f"UC{abs(hash(base)) % 10**22:022d}"[:24],
        "snippet": {
            "title": f"Mock {base.title()} Channel",
            "description": "Deterministic mock channel for tests.",
            "customUrl": f"@{base}",
            "thumbnails": {"default": {"url": f"https://example.com/{base}.jpg"}},
        },
        "statistics": {
            "viewCount": str(150_000 + abs(hash(base)) % 50_000),
            "subscriberCount": str(2_400 + abs(hash(base)) % 1_000),
            "videoCount": str(42 + abs(hash(base)) % 30),
        },
    }


def _mock_videos(channel_id: str, limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i in range(limit):
        seed = f"{channel_id}:{i}"
        out.append(
            {
                "id": f"vid_{abs(hash(seed)) % 10**11:011d}",
                "title": f"Mock video #{i + 1}",
                "published_at": f"2026-04-{(i % 28) + 1:02d}T12:00:00Z",
                "view_count": 1_200 + abs(hash(seed)) % 8_000,
                "like_count": 50 + abs(hash(seed)) % 500,
                "comment_count": abs(hash(seed)) % 80,
                "thumbnail_url": f"https://example.com/thumb_{i}.jpg",
            }
        )
    return out


# ─────────── Public API ───────────


async def get_channel(
    db: AsyncSession, *, handle: str | None = None, channel_id: str | None = None
) -> dict[str, Any]:
    """Resolve a channel by @handle or by UCxxxx id."""
    if not handle and not channel_id:
        raise YouTubeError("handle or channel_id is required")
    if _is_mock_mode():
        return _mock_channel(handle or channel_id or "channel")
    api_key = await _api_key(db)
    if not api_key:
        raise YouTubeError("YouTube api_key is not configured")

    params: dict[str, Any] = {
        "part": "snippet,statistics",
        "key": api_key,
    }
    if channel_id:
        params["id"] = channel_id
    else:
        params["forHandle"] = handle

    data = await _call("channels", params)
    items = data.get("items") or []
    if not items:
        raise YouTubeError("Channel not found")
    item = items[0]
    if not isinstance(item, dict):
        raise YouTubeError("Unexpected channel item shape")
    return item


async def list_recent_videos(
    db: AsyncSession, *, channel_id: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Return the channel's most recent uploads with stats."""
    if _is_mock_mode():
        return _mock_videos(channel_id, limit)
    api_key = await _api_key(db)
    if not api_key:
        raise YouTubeError("YouTube api_key is not configured")

    search = await _call(
        "search",
        {
            "part": "id",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": limit,
            "key": api_key,
        },
    )
    items = search.get("items") or []
    video_ids = [
        i.get("id", {}).get("videoId")
        for i in items
        if isinstance(i, dict) and i.get("id", {}).get("videoId")
    ]
    if not video_ids:
        return []

    details = await _call(
        "videos",
        {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": api_key,
        },
    )
    out: list[dict[str, Any]] = []
    for v in details.get("items") or []:
        if not isinstance(v, dict):
            continue
        snippet = v.get("snippet") or {}
        stats = v.get("statistics") or {}
        out.append(
            {
                "id": v.get("id"),
                "title": snippet.get("title") or "—",
                "published_at": snippet.get("publishedAt"),
                "view_count": int(stats.get("viewCount") or 0),
                "like_count": int(stats.get("likeCount") or 0),
                "comment_count": int(stats.get("commentCount") or 0),
                "thumbnail_url": (snippet.get("thumbnails") or {})
                .get("default", {})
                .get("url"),
            }
        )
    return out


async def aggregate_stats(
    db: AsyncSession, *, channel_id: str
) -> dict[str, int | str]:
    """Quick channel-wide stats for a dashboard card."""
    channel = await get_channel(db, channel_id=channel_id)
    stats = channel.get("statistics") or {}
    return {
        "subscribers": int(stats.get("subscriberCount") or 0),
        "views": int(stats.get("viewCount") or 0),
        "videos": int(stats.get("videoCount") or 0),
        "title": (channel.get("snippet") or {}).get("title") or "",
    }


__all__ = [
    "YouTubeError",
    "aggregate_stats",
    "get_channel",
    "list_recent_videos",
]
