"""Compose prompts for the post generator: brand voice + RAG + platform rules."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import Brand
from app.services import knowledge_service

PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPT_PATH = PROMPTS_DIR / "post_generator.txt"

# Platform-specific output guidance. Kept short — the model already knows
# the format, we mostly clarify limits and required style.
PLATFORM_RULES: dict[str, str] = {
    "telegram": (
        "- Telegram channel post.\n"
        "- Up to 4096 characters; keep it tight (200-800 chars is ideal).\n"
        "- Plain text + emojis. Up to 5 hashtags at the bottom.\n"
        "- One clear call to action."
    ),
    "instagram": (
        "- Instagram feed caption.\n"
        "- Up to 2200 characters; first line is the hook (no preface).\n"
        "- Use line breaks generously. Up to 30 hashtags grouped at the end.\n"
        "- Aim for emotional + informative tone."
    ),
    "facebook": (
        "- Facebook page post.\n"
        "- Keep the first 60 characters punchy - they show in feed previews.\n"
        "- 3-8 hashtags, woven naturally or grouped at the end.\n"
        "- Include a clear next step (link, DM, comment)."
    ),
    "youtube": (
        "- YouTube video description.\n"
        "- First 2 lines are the hook (above 'Show more').\n"
        "- Up to 5000 characters. Sections OK. Up to 15 hashtags."
    ),
}

DEFAULT_PLATFORM_RULES = "- Generic social-media post.\n" "- 200-800 characters. 3-8 hashtags."


def _platform_rules(platform: str) -> str:
    return PLATFORM_RULES.get(platform.lower(), DEFAULT_PLATFORM_RULES)


def _load_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def load_prompt_text(template_name: str) -> str:
    return (PROMPTS_DIR / template_name).read_text(encoding="utf-8")


def render_prompt(template_name: str, values: Mapping[str, object]) -> str:
    rendered = load_prompt_text(template_name)
    for key, value in values.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


async def _rag_context(
    db: AsyncSession, *, brand_id: UUID, query: str, top_k: int = 4
) -> tuple[str, list[str]]:
    """Pull top-k chunks for the prompt and return their ids for traceability."""
    if not query.strip():
        return "(no relevant knowledge base context)", []
    try:
        hits = await knowledge_service.search(db, query=query, brand_id=brand_id, top_k=top_k)
    except Exception:
        return "(knowledge base search failed — proceed without it)", []
    if not hits:
        return "(no relevant knowledge base context)", []
    lines: list[str] = []
    chunk_ids: list[str] = []
    for h in hits:
        chunk_ids.append(h["chunk_id"])
        title = h.get("document_title") or "—"
        lines.append(f"[{title}] {h['content'].strip()}")
    return "\n\n".join(lines), chunk_ids


async def build_prompt(
    db: AsyncSession,
    *,
    brand: Brand,
    platform: str,
    user_goal: str,
    output_language: str = "uz",
) -> tuple[str, list[str]]:
    """Return (rendered_prompt, rag_chunk_ids).

    The prompt template uses ``{name}`` placeholders — we keep it simple
    with ``str.replace`` to avoid surprises from user-supplied braces.
    """
    rag_text, chunk_ids = await _rag_context(db, brand_id=brand.id, query=user_goal)
    languages = ", ".join(brand.languages or ["uz"])
    rendered = render_prompt(
        "post_generator.txt",
        {
            "brand_name": brand.name,
            "brand_industry": brand.industry or "—",
            "brand_voice": brand.voice_tone or "Friendly, professional",
            "brand_audience": brand.target_audience or "—",
            "brand_languages": languages,
            "platform": platform,
            "platform_rules": _platform_rules(platform),
            "user_goal": user_goal.strip() or "—",
            "rag_context": rag_text,
            "output_language": output_language,
        },
    )
    return rendered, chunk_ids


__all__ = ["PLATFORM_RULES", "build_prompt", "load_prompt_text", "render_prompt"]
