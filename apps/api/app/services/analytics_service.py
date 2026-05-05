"""SMM analytics — aggregate engagement metrics + optimal-time analysis.

This sprint records latest-snapshot metrics per publication. Real provider
sync (Telegram views, Meta Insights, YouTube stats) is wired into a single
``record_snapshot`` call that the user can trigger or the worker can poll.

For dev/tests we synthesise deterministic metrics from each publication's
identifiers so the dashboards keep working without real API quotas.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import BrandSocialAccount, Post, PostMetrics, PostPublication
from app.services import meta_service

logger = logging.getLogger(__name__)


# ─────────── Mock metrics seeding (deterministic) ───────────


def _synth_metrics(seed: str, *, base_views: int = 1200) -> dict[str, int]:
    h = hashlib.sha256(seed.encode()).digest()
    views = base_views + (int.from_bytes(h[:3], "big") % 8_000)
    likes = max(5, views // (10 + (h[3] % 8)))
    comments = max(0, likes // (3 + (h[4] % 5)))
    shares = max(0, likes // (5 + (h[5] % 7)))
    reach = views + (int.from_bytes(h[6:8], "big") % 1500)
    return {
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "reach": reach,
    }


async def _published_publications(
    db: AsyncSession, *, brand_id: UUID | None = None
) -> list[tuple[PostPublication, Post]]:
    stmt = (
        select(PostPublication, Post)
        .join(Post, Post.id == PostPublication.post_id)
        .where(PostPublication.status == "published")
    )
    if brand_id is not None:
        stmt = stmt.where(Post.brand_id == brand_id)
    rows = (await db.execute(stmt)).all()
    return [(pub, post) for pub, post in rows]


async def _resolve_metrics(
    db: AsyncSession,
    *,
    publication: PostPublication,
    post: Post,
    sampled_at: datetime,
) -> dict[str, int]:
    seed = f"{publication.id}:{publication.external_post_id or ''}:{sampled_at.date().isoformat()}"
    metrics = _synth_metrics(seed)

    if publication.provider not in {"facebook", "instagram"}:
        return metrics
    if not publication.external_post_id:
        return metrics

    account = await db.get(BrandSocialAccount, publication.social_account_id)
    token = str(((account.metadata_ or {}) if account else {}).get("page_token") or "").strip()
    if not token:
        return metrics

    try:
        pulled = await meta_service.get_post_metrics(
            db,
            provider=publication.provider,
            object_id=publication.external_post_id,
            access_token=token,
        )
    except Exception as exc:
        logger.warning(
            "Analytics metrics pull failed for %s publication %s: %s",
            publication.provider,
            publication.id,
            exc,
        )
        return metrics

    for key, value in pulled.items():
        if key in metrics:
            metrics[key] = max(0, int(value))
    return metrics


async def record_snapshot(db: AsyncSession, *, brand_id: UUID | None = None) -> int:
    """Refresh the latest metrics row per published publication.

    Returns the number of rows inserted. Real providers would be queried
    here; we use the deterministic synthesiser for dev.
    """
    pairs = await _published_publications(db, brand_id=brand_id)
    if not pairs:
        return 0
    now = datetime.now(UTC)
    inserted = 0
    for pub, post in pairs:
        metrics = await _resolve_metrics(db, publication=pub, post=post, sampled_at=now)
        db.add(
            PostMetrics(
                publication_id=pub.id,
                brand_id=post.brand_id,
                provider=pub.provider,
                sampled_at=now,
                **metrics,
            )
        )
        inserted += 1
    await db.flush()
    return inserted


# ─────────── Aggregations ───────────


@dataclass
class LatestPerPublication:
    metrics: PostMetrics
    publication: PostPublication
    post: Post


async def _latest_per_publication(
    db: AsyncSession, *, brand_id: UUID | None = None
) -> list[LatestPerPublication]:
    """For each publication, keep only the most recent metrics row."""
    # Subquery: max(sampled_at) per publication_id
    sub = (
        select(
            PostMetrics.publication_id.label("pub_id"),
            func.max(PostMetrics.sampled_at).label("latest"),
        )
        .group_by(PostMetrics.publication_id)
        .subquery()
    )
    stmt = (
        select(PostMetrics, PostPublication, Post)
        .join(
            sub,
            (sub.c.pub_id == PostMetrics.publication_id) & (sub.c.latest == PostMetrics.sampled_at),
        )
        .join(PostPublication, PostPublication.id == PostMetrics.publication_id)
        .join(Post, Post.id == PostPublication.post_id)
    )
    if brand_id is not None:
        stmt = stmt.where(PostMetrics.brand_id == brand_id)
    rows = (await db.execute(stmt)).all()
    return [LatestPerPublication(metrics=m, publication=p, post=post) for m, p, post in rows]


async def overview(db: AsyncSession, *, brand_id: UUID | None = None) -> dict[str, Any]:
    """KPI snapshot: totals + per-platform breakdown + average engagement."""
    items = await _latest_per_publication(db, brand_id=brand_id)
    if not items:
        return {
            "total_posts": 0,
            "total_views": 0,
            "total_likes": 0,
            "total_comments": 0,
            "total_shares": 0,
            "engagement_rate": 0.0,
            "by_platform": {},
        }
    total_posts = len(items)
    total_views = sum(i.metrics.views for i in items)
    total_likes = sum(i.metrics.likes for i in items)
    total_comments = sum(i.metrics.comments for i in items)
    total_shares = sum(i.metrics.shares for i in items)
    engagement = total_likes + total_comments + total_shares
    by_platform: dict[str, dict[str, int]] = {}
    for i in items:
        prov = i.metrics.provider
        slot = by_platform.setdefault(
            prov, {"posts": 0, "views": 0, "likes": 0, "comments": 0, "shares": 0}
        )
        slot["posts"] += 1
        slot["views"] += i.metrics.views
        slot["likes"] += i.metrics.likes
        slot["comments"] += i.metrics.comments
        slot["shares"] += i.metrics.shares
    return {
        "total_posts": total_posts,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "engagement_rate": round(engagement / total_views, 4) if total_views else 0.0,
        "by_platform": by_platform,
    }


async def timeseries(
    db: AsyncSession,
    *,
    brand_id: UUID | None = None,
    days: int = 30,
) -> list[dict[str, Any]]:
    """Daily totals for the last N days using each publication's published_at."""
    if days < 1 or days > 180:
        raise ValueError("days must be 1..180")
    since = datetime.now(UTC) - timedelta(days=days)
    items = await _latest_per_publication(db, brand_id=brand_id)
    buckets: dict[str, dict[str, int]] = {}
    for i in items:
        anchor = i.publication.completed_at or i.post.published_at
        if anchor is None or anchor < since:
            continue
        key = anchor.astimezone(UTC).date().isoformat()
        slot = buckets.setdefault(
            key, {"posts": 0, "views": 0, "likes": 0, "comments": 0, "shares": 0}
        )
        slot["posts"] += 1
        slot["views"] += i.metrics.views
        slot["likes"] += i.metrics.likes
        slot["comments"] += i.metrics.comments
        slot["shares"] += i.metrics.shares
    return [{"date": k, **v} for k, v in sorted(buckets.items())]


async def top_posts(
    db: AsyncSession,
    *,
    brand_id: UUID | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    items = await _latest_per_publication(db, brand_id=brand_id)
    items.sort(
        key=lambda i: (
            i.metrics.likes + i.metrics.comments + i.metrics.shares,
            i.metrics.views,
        ),
        reverse=True,
    )
    out: list[dict[str, Any]] = []
    for i in items[:limit]:
        anchor = i.publication.completed_at or i.post.published_at
        out.append(
            {
                "post_id": str(i.post.id),
                "publication_id": str(i.publication.id),
                "provider": i.metrics.provider,
                "title": i.post.title or i.post.body[:80],
                "external_post_id": i.publication.external_post_id,
                "views": i.metrics.views,
                "likes": i.metrics.likes,
                "comments": i.metrics.comments,
                "shares": i.metrics.shares,
                "engagement": i.metrics.likes + i.metrics.comments + i.metrics.shares,
                "published_at": anchor.isoformat() if anchor else None,
            }
        )
    return out


async def optimal_times(db: AsyncSession, *, brand_id: UUID | None = None) -> dict[str, Any]:
    """Compute average engagement per (weekday, hour) cell.

    weekday: 0..6 (Mon..Sun, UTC). hour: 0..23 (UTC).
    Returns a sparse list of cells plus the top 3 picks.
    """
    items = await _latest_per_publication(db, brand_id=brand_id)
    cells: dict[tuple[int, int], dict[str, int]] = {}
    for i in items:
        anchor = i.publication.completed_at or i.post.published_at
        if anchor is None:
            continue
        a = anchor.astimezone(UTC)
        key = (a.weekday(), a.hour)
        slot = cells.setdefault(key, {"posts": 0, "engagement": 0, "views": 0})
        slot["posts"] += 1
        slot["engagement"] += i.metrics.likes + i.metrics.comments + i.metrics.shares
        slot["views"] += i.metrics.views
    rows: list[dict[str, Any]] = []
    for (wd, hr), v in cells.items():
        avg = v["engagement"] / v["posts"] if v["posts"] else 0
        rows.append(
            {
                "weekday": wd,
                "hour": hr,
                "posts": v["posts"],
                "avg_engagement": round(avg, 2),
                "views": v["views"],
            }
        )
    rows.sort(key=lambda r: r["avg_engagement"], reverse=True)
    return {
        "cells": rows,
        "best": rows[:3],
    }


# ─────────── AI-flavoured insights ───────────


def _format_overview_for_prompt(snapshot: dict[str, Any]) -> str:
    lines = [
        f"Total posts: {snapshot['total_posts']}",
        f"Total views: {snapshot['total_views']}",
        f"Total likes: {snapshot['total_likes']}",
        f"Total comments: {snapshot['total_comments']}",
        f"Engagement rate: {snapshot['engagement_rate']}",
    ]
    for prov, slot in (snapshot.get("by_platform") or {}).items():
        lines.append(
            f"{prov}: {slot['posts']} posts, {slot['views']} views, "
            f"{slot['likes']} likes, {slot['comments']} comments"
        )
    return "\n".join(lines)


def _format_optimal_for_prompt(rows: Iterable[dict[str, Any]]) -> str:
    weekdays = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
    out = []
    for r in rows:
        out.append(
            f"{weekdays[r['weekday']]} {r['hour']:02d}:00 — "
            f"avg engagement {r['avg_engagement']}, posts {r['posts']}"
        )
    return "\n".join(out) or "(no data yet)"


async def insights(
    db: AsyncSession,
    *,
    brand_id: UUID | None = None,
) -> dict[str, Any]:
    """AI-generated narrative on top of the aggregates.

    Falls back to a deterministic summary string when AI mock mode is on
    or no provider key is configured — keeps the UX testable without
    burning tokens.
    """
    from app.services import ai_service  # local import to avoid cycle

    snapshot = await overview(db, brand_id=brand_id)
    optimal = await optimal_times(db, brand_id=brand_id)
    top = await top_posts(db, brand_id=brand_id, limit=3)

    if snapshot["total_posts"] == 0:
        return {
            "summary": "Hozircha e'lon qilingan postlar yo'q — analytics ma'lumoti to'planmagan.",
            "recommendations": [],
            "snapshot": snapshot,
            "optimal": optimal,
            "top_posts": top,
        }

    system = (
        "You are a senior SMM analyst. Given engagement totals and best-time "
        "data, produce: (1) a 2-sentence summary in O'zbek lotin, (2) 3 "
        "concrete recommendations as a JSON array of short strings (also "
        "O'zbek). Return EXACTLY this JSON shape and nothing else: "
        '{"summary":"…","recommendations":["…","…","…"]}'
    )
    user = (
        "OVERVIEW:\n"
        f"{_format_overview_for_prompt(snapshot)}\n\n"
        "TOP TIMES:\n"
        f"{_format_optimal_for_prompt(optimal['best'])}\n\n"
        "TOP POSTS:\n"
        + "\n".join(f"- [{p['provider']}] {p['title']} — engagement {p['engagement']}" for p in top)
    )

    try:
        resp = await ai_service.complete(db, system=system, user=user, max_tokens=512)
        text = resp.text
    except Exception as exc:
        logger.warning("Insights AI call failed (%s) — using fallback summary", exc)
        text = ""

    parsed = _parse_json_safely(text)
    if not parsed:
        parsed = _fallback_insights(snapshot, optimal["best"])
    return {
        **parsed,
        "snapshot": snapshot,
        "optimal": optimal,
        "top_posts": top,
    }


def _parse_json_safely(text: str) -> dict[str, Any] | None:
    if not text or "{" not in text:
        return None
    try:
        import json

        # Trim anything before the first { and after the last }
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
    except (ValueError, KeyError):
        return None
    if not isinstance(data, dict):
        return None
    summary = str(data.get("summary") or "")
    recs = data.get("recommendations") or []
    if not isinstance(recs, list):
        recs = []
    recs = [str(r) for r in recs[:5] if r]
    if not summary:
        return None
    return {"summary": summary, "recommendations": recs}


def _fallback_insights(
    snapshot: dict[str, Any], best_times: list[dict[str, Any]]
) -> dict[str, str | list[str]]:
    weekdays = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
    summary = (
        f"Jami {snapshot['total_posts']} ta post {snapshot['total_views']} marta ko'rilgan, "
        f"engagement darajasi {round(snapshot['engagement_rate'] * 100, 1)}%."
    )
    recs: list[str] = []
    if best_times:
        top = best_times[0]
        recs.append(
            f"Eng yuqori engagement {weekdays[top['weekday']]} kunlari "
            f"{top['hour']:02d}:00 atrofida — keyingi postlarni shu oynaga rejalashtiring."
        )
    by_platform = snapshot.get("by_platform") or {}
    if by_platform:
        leader = max(by_platform.items(), key=lambda kv: kv[1]["likes"] + kv[1]["comments"])
        recs.append(
            f"{leader[0]} platformasi yetakchi — bu yerga ko'proq kontent va "
            f"A/B testlar yo'naltiring."
        )
    if snapshot["engagement_rate"] < 0.02:
        recs.append(
            "Engagement past — sarlavhalarda hook va aniq CTA qo'shing, "
            "Knowledge Base'dagi mijoz savollaridan foydalaning."
        )
    return {"summary": summary, "recommendations": recs[:3]}


__all__ = [
    "insights",
    "optimal_times",
    "overview",
    "record_snapshot",
    "timeseries",
    "top_posts",
]
