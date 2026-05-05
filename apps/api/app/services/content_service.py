"""AI content generation lifecycle.

generate_post() orchestrates: load brand → build prompt (with RAG) → check
24h cache (by stable cache_key) → call ai_service → persist ContentDraft.

Drafts are returned as the canonical output; later sprints turn them into
Posts (scheduled / published).
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompt_builder import build_prompt, load_prompt_text, render_prompt
from app.models.smm import Brand, ContentDraft
from app.services import ai_service, knowledge_service

SYSTEM_GUARDRAILS = load_prompt_text("system_guardrails.txt")
ASSISTANT_GUARDRAILS = load_prompt_text("assistant_guardrails.txt")

CACHE_TTL_HOURS = 24

VARIANT_STYLES = (
    "Variant A: short, energetic, 50-100 words, one strong CTA.",
    "Variant B: story-led, emotional, 150-250 words, natural CTA.",
    "Variant C: expert-advice angle, structured list, trust-building CTA.",
    "Variant D: bold promo angle, urgency without false scarcity.",
    "Variant E: educational carousel-style copy with clear takeaway.",
)


def _cache_key(brand_id: UUID, platform: str, language: str, user_goal: str) -> str:
    """Stable hash so identical requests within TTL reuse the cached draft."""
    norm = f"{brand_id}|{platform}|{language}|{user_goal.strip().lower()}"
    return hashlib.sha256(norm.encode()).hexdigest()[:48]


async def _get_brand(db: AsyncSession, brand_id: UUID) -> Brand:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")
    return brand


def _brand_context(brand: Brand) -> str:
    languages = ", ".join(brand.languages or ["uz"])
    return "\n".join(
        [
            f"Brand: {brand.name}",
            f"Industry: {brand.industry or '-'}",
            f"Voice: {brand.voice_tone or 'Friendly, professional'}",
            f"Audience: {brand.target_audience or '-'}",
            f"Languages: {languages}",
        ]
    )


async def _rag_snippets(
    db: AsyncSession, *, brand_id: UUID, query: str, top_k: int = 4
) -> tuple[str, list[str]]:
    if not query.strip():
        return "(no relevant knowledge base context)", []
    try:
        hits = await knowledge_service.search(db, query=query, brand_id=brand_id, top_k=top_k)
    except Exception:
        return "(knowledge base search failed - proceed without it)", []
    if not hits:
        return "(no relevant knowledge base context)", []
    lines: list[str] = []
    chunk_ids: list[str] = []
    for hit in hits:
        chunk_ids.append(str(hit["chunk_id"]))
        title = hit.get("document_title") or "-"
        lines.append(f"[{title}] {str(hit['content']).strip()}")
    return "\n\n".join(lines), chunk_ids


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
    brand = await _get_brand(db, brand_id)

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


async def generate_variants(
    db: AsyncSession,
    *,
    brand_id: UUID,
    platform: str,
    user_goal: str,
    language: str,
    user_id: UUID,
    title: str | None = None,
    variants: int = 3,
    use_cache: bool = True,
) -> list[ContentDraft]:
    if variants < 1 or variants > len(VARIANT_STYLES):
        raise ValueError(f"variants must be 1..{len(VARIANT_STYLES)}")

    out: list[ContentDraft] = []
    base_title = title.strip() if title else user_goal.strip()[:64]
    for idx, style in enumerate(VARIANT_STYLES[:variants]):
        letter = chr(ord("A") + idx)
        variant_goal = f"{user_goal.strip()}\n\n{style}"
        draft = await generate_post(
            db,
            brand_id=brand_id,
            platform=platform,
            user_goal=variant_goal,
            language=language,
            user_id=user_id,
            title=f"{base_title} - Variant {letter}",
            use_cache=use_cache,
        )
        out.append(draft)
    return out


async def improve_content(
    db: AsyncSession,
    *,
    draft_id: UUID,
    instruction: str,
    user_id: UUID,
    selected_text: str | None = None,
) -> ContentDraft:
    draft = await get_draft(db, draft_id)
    if draft is None:
        raise ValueError("Draft not found")
    brand = await _get_brand(db, draft.brand_id)
    target = (selected_text or draft.body).strip()
    if not target:
        raise ValueError("Draft body is empty")

    rag_text, chunk_ids = await _rag_snippets(db, brand_id=brand.id, query=instruction)
    selected_note = (
        "The user selected this exact fragment. Return the FULL draft with only this "
        "fragment improved where possible."
        if selected_text
        else "Return the FULL improved draft."
    )
    prompt = render_prompt(
        "improve_content.txt",
        {
            "brand_context": _brand_context(brand),
            "platform": draft.platform,
            "language": draft.language,
            "rag_context": rag_text,
            "current_draft": draft.body,
            "target_text": target,
            "instruction": instruction.strip(),
            "selected_note": selected_note,
        },
    )
    response = await ai_service.complete(db, system=SYSTEM_GUARDRAILS, user=prompt, max_tokens=1400)

    draft.body = response.text
    draft.provider = response.provider
    draft.model = response.model
    draft.tokens_used = int(draft.tokens_used or 0) + response.total_tokens
    draft.rag_chunk_ids = chunk_ids or draft.rag_chunk_ids
    draft.cache_key = None
    await db.flush()
    return draft


async def chat(
    db: AsyncSession,
    *,
    brand_id: UUID,
    message: str,
    language: str,
    history: list[dict[str, str]] | None = None,
    draft_id: UUID | None = None,
) -> dict[str, Any]:
    brand = await _get_brand(db, brand_id)
    draft = await get_draft(db, draft_id) if draft_id else None
    if draft_id and draft is None:
        raise ValueError("Draft not found")

    rag_text, chunk_ids = await _rag_snippets(db, brand_id=brand_id, query=message)
    history_lines = []
    for item in (history or [])[-10:]:
        role = item.get("role") or "user"
        content = (item.get("content") or "").strip()
        if content:
            history_lines.append(f"{role}: {content}")
    prompt = render_prompt(
        "ai_chat.txt",
        {
            "brand_context": _brand_context(brand),
            "language": language,
            "rag_context": rag_text,
            "current_draft": draft.body if draft else "-",
            "recent_chat": "\n".join(history_lines) if history_lines else "-",
            "message": message.strip(),
        },
    )
    response = await ai_service.complete(
        db, system=ASSISTANT_GUARDRAILS, user=prompt, max_tokens=1200
    )
    return {
        "text": response.text,
        "provider": response.provider,
        "model": response.model,
        "tokens_used": response.total_tokens,
        "rag_chunk_ids": chunk_ids or None,
    }


def _extract_hashtags(text: str, *, count: int) -> list[str]:
    seen: set[str] = set()
    tags: list[str] = []
    for raw in re.findall(r"#[\w'-]+", text.lower()):
        tag = "#" + re.sub(r"[^a-z0-9_'-]", "", raw.removeprefix("#"))
        if len(tag) <= 1 or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
        if len(tags) >= count:
            return tags
    return tags


def _fallback_hashtags(brand: Brand, topic: str, *, count: int) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", f"{brand.name} {brand.industry or ''} {topic}".lower())
    candidates = [f"#{word}" for word in words if len(word) > 2]
    candidates.extend(["#uzbekiston", "#toshkent", "#nexusai", "#smm"])
    out: list[str] = []
    for tag in candidates:
        if tag not in out:
            out.append(tag)
        if len(out) >= count:
            break
    return out


async def generate_hashtags(
    db: AsyncSession,
    *,
    brand_id: UUID,
    platform: str,
    topic: str,
    language: str,
    count: int,
) -> dict[str, Any]:
    brand = await _get_brand(db, brand_id)
    rag_text, chunk_ids = await _rag_snippets(db, brand_id=brand_id, query=topic)
    prompt = render_prompt(
        "generate_hashtags.txt",
        {
            "brand_context": _brand_context(brand),
            "platform": platform,
            "language": language,
            "topic": topic.strip(),
            "rag_context": rag_text,
            "count": count,
        },
    )
    response = await ai_service.complete(
        db, system=ASSISTANT_GUARDRAILS, user=prompt, max_tokens=500
    )
    hashtags = _extract_hashtags(response.text, count=count)
    for tag in _fallback_hashtags(brand, topic, count=count):
        if len(hashtags) >= count:
            break
        if tag not in hashtags:
            hashtags.append(tag)
    return {
        "text": " ".join(hashtags),
        "hashtags": hashtags[:count],
        "provider": response.provider,
        "model": response.model,
        "tokens_used": response.total_tokens,
        "rag_chunk_ids": chunk_ids or None,
    }


async def generate_reels_script(
    db: AsyncSession,
    *,
    brand_id: UUID,
    topic: str,
    language: str,
    duration_seconds: int,
) -> dict[str, Any]:
    brand = await _get_brand(db, brand_id)
    rag_text, chunk_ids = await _rag_snippets(db, brand_id=brand_id, query=topic)
    prompt = render_prompt(
        "generate_reels_script.txt",
        {
            "brand_context": _brand_context(brand),
            "language": language,
            "duration_seconds": duration_seconds,
            "topic": topic.strip(),
            "rag_context": rag_text,
        },
    )
    response = await ai_service.complete(
        db, system=ASSISTANT_GUARDRAILS, user=prompt, max_tokens=1600
    )
    return {
        "text": response.text,
        "provider": response.provider,
        "model": response.model,
        "tokens_used": response.total_tokens,
        "rag_chunk_ids": chunk_ids or None,
    }


async def generate_30_day_plan(
    db: AsyncSession,
    *,
    brand_id: UUID,
    platform: str,
    topic: str,
    language: str,
    days: int,
) -> dict[str, Any]:
    brand = await _get_brand(db, brand_id)
    rag_text, chunk_ids = await _rag_snippets(db, brand_id=brand_id, query=topic)
    prompt = render_prompt(
        "generate_30_day_plan.txt",
        {
            "brand_context": _brand_context(brand),
            "platform": platform,
            "language": language,
            "days": days,
            "topic": topic.strip(),
            "rag_context": rag_text,
        },
    )
    response = await ai_service.complete(
        db, system=ASSISTANT_GUARDRAILS, user=prompt, max_tokens=2200
    )
    return {
        "text": response.text,
        "provider": response.provider,
        "model": response.model,
        "tokens_used": response.total_tokens,
        "rag_chunk_ids": chunk_ids or None,
    }


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
    "chat",
    "delete_draft",
    "generate_30_day_plan",
    "generate_hashtags",
    "generate_post",
    "generate_reels_script",
    "generate_variants",
    "get_draft",
    "improve_content",
    "list_drafts",
    "stats",
    "toggle_star",
    "update_draft",
]
