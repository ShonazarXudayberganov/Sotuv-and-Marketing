"""AI content generation lifecycle.

generate_post() orchestrates: load brand → build prompt (with RAG) → check
24h cache (by stable cache_key) → call ai_service → persist ContentDraft.

Drafts are returned as the canonical output; later sprints turn them into
Posts (scheduled / published).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompt_builder import build_prompt
from app.models.smm import Brand, ContentDraft
from app.services import ai_service

SYSTEM_GUARDRAILS = (
    "You are NEXUS AI, an SMM copywriter. Always obey platform constraints, "
    "never invent facts not present in the knowledge base context, and respond "
    "only with the post body — no preface, no markdown headers, no labels."
)

CACHE_TTL_HOURS = 24


def _cache_key(brand_id: UUID, platform: str, language: str, user_goal: str) -> str:
    """Stable hash so identical requests within TTL reuse the cached draft."""
    norm = f"{brand_id}|{platform}|{language}|{user_goal.strip().lower()}"
    return hashlib.sha256(norm.encode()).hexdigest()[:48]


async def _find_cached(db: AsyncSession, *, cache_key: str) -> ContentDraft | None:
    stmt = (
        select(ContentDraft)
        .where(ContentDraft.cache_key == cache_key)
        .order_by(desc(ContentDraft.created_at))
        .limit(1)
    )
    rec = (await db.execute(stmt)).scalars().first()
    if rec is None:
        return None
    age_seconds = (datetime.now(UTC) - rec.created_at).total_seconds()
    if age_seconds > CACHE_TTL_HOURS * 3600:
        return None
    return rec


async def generate_post(
    db: AsyncSession,
    *,
    brand_id: UUID,
    platform: str,
    user_goal: str,
    language: str,
    user_id: UUID,
    title: str | None = None,
    use_cache: bool = True,
) -> ContentDraft:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")

    cache_key = _cache_key(brand_id, platform, language, user_goal)

    if use_cache:
        cached = await _find_cached(db, cache_key=cache_key)
        if cached is not None:
            return cached

    rendered_prompt, chunk_ids = await build_prompt(
        db, brand=brand, platform=platform, user_goal=user_goal, output_language=language
    )

    response = await ai_service.complete(db, system=SYSTEM_GUARDRAILS, user=rendered_prompt)

    draft = ContentDraft(
        brand_id=brand_id,
        platform=platform,
        title=title,
        body=response.text,
        user_goal=user_goal,
        language=language,
        provider=response.provider,
        model=response.model,
        tokens_used=response.total_tokens,
        rag_chunk_ids=chunk_ids or None,
        cache_key=cache_key,
        created_by=user_id,
    )
    db.add(draft)
    await db.flush()
    return draft


async def list_drafts(
    db: AsyncSession,
    *,
    brand_id: UUID | None = None,
    platform: str | None = None,
    starred: bool | None = None,
    limit: int = 50,
) -> list[ContentDraft]:
    stmt = select(ContentDraft).order_by(desc(ContentDraft.created_at)).limit(limit)
    if brand_id is not None:
        stmt = stmt.where(ContentDraft.brand_id == brand_id)
    if platform is not None:
        stmt = stmt.where(ContentDraft.platform == platform)
    if starred is True:
        stmt = stmt.where(ContentDraft.is_starred.is_(True))
    return list((await db.execute(stmt)).scalars())


async def get_draft(db: AsyncSession, draft_id: UUID) -> ContentDraft | None:
    return await db.get(ContentDraft, draft_id)


async def toggle_star(db: AsyncSession, draft_id: UUID) -> ContentDraft | None:
    rec = await db.get(ContentDraft, draft_id)
    if rec is None:
        return None
    rec.is_starred = not rec.is_starred
    await db.flush()
    return rec


async def update_draft(
    db: AsyncSession,
    draft_id: UUID,
    *,
    title: str | None = None,
    body: str | None = None,
) -> ContentDraft | None:
    rec = await db.get(ContentDraft, draft_id)
    if rec is None:
        return None
    if title is not None:
        rec.title = title
    if body is not None:
        rec.body = body
        # Manual edits invalidate the cache so future calls regenerate.
        rec.cache_key = None
    await db.flush()
    return rec


async def delete_draft(db: AsyncSession, draft_id: UUID) -> bool:
    rec = await db.get(ContentDraft, draft_id)
    if rec is None:
        return False
    await db.delete(rec)
    await db.flush()
    return True


async def stats(db: AsyncSession) -> dict[str, Any]:
    """Quick counts for the AI studio dashboard."""
    total = (await db.execute(select(ContentDraft))).scalars().all()
    return {
        "drafts_total": len(total),
        "drafts_starred": sum(1 for d in total if d.is_starred),
        "by_platform": {
            p: sum(1 for d in total if d.platform == p) for p in {d.platform for d in total}
        },
    }


__all__ = [
    "delete_draft",
    "generate_post",
    "get_draft",
    "list_drafts",
    "stats",
    "toggle_star",
    "update_draft",
]
