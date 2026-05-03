"""AI auto-reply: turns an incoming inbox message into a draft AI response.

Uses the brand's voice + RAG knowledge base context. Returns confidence (0..100)
so the caller can decide whether to send automatically (>= threshold) or just
suggest. Mock fallback keeps the dev loop deterministic without burning tokens.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inbox import Conversation, Message
from app.models.smm import Brand
from app.services import ai_service, knowledge_service

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "ai" / "prompts" / "auto_reply.txt"

SYSTEM_GUARDRAILS = (
    "You are NEXUS AI auto-reply. Always obey the rules in the user "
    "prompt and respond ONLY with the JSON object specified — no prose, "
    "no markdown."
)


@dataclass
class AutoReplyResult:
    reply: str
    confidence: int
    mocked: bool


def _is_mock_mode() -> bool:
    return os.getenv("AI_MOCK", "false").lower() in {"1", "true", "yes"}


def _load_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


async def _history(db: AsyncSession, conversation_id: UUID, limit: int = 6) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(desc(Message.occurred_at))
        .limit(limit)
    )
    rows = list((await db.execute(stmt)).scalars())
    return list(reversed(rows))


def _format_history(rows: list[Message]) -> str:
    if not rows:
        return "(no prior messages)"
    lines: list[str] = []
    for m in rows:
        speaker = "Customer" if m.direction == "in" else ("AI" if m.is_auto_reply else "Agent")
        lines.append(f"{speaker}: {m.body.strip()[:280]}")
    return "\n".join(lines)


async def _rag_context(db: AsyncSession, *, brand_id: UUID | None, query: str) -> str:
    if brand_id is None or not query.strip():
        return "(no relevant knowledge base context)"
    try:
        hits = await knowledge_service.search(db, query=query, brand_id=brand_id, top_k=4)
    except Exception:
        return "(knowledge base search failed — proceed without it)"
    if not hits:
        return "(no relevant knowledge base context)"
    return "\n\n".join(f"[{h.get('document_title') or '—'}] {h['content'].strip()}" for h in hits)


def _mock_reply(incoming: str) -> AutoReplyResult:
    text = incoming.strip().lower()
    if any(word in text for word in ("salom", "hello", "assalomu")):
        return AutoReplyResult(
            "Assalomu alaykum! NEXUS AI yordamchisiman, savolingiz bo'yicha "
            "yordam bera olamanmi?",
            confidence=92,
            mocked=True,
        )
    if any(word in text for word in ("narx", "price", "сколько")):
        return AutoReplyResult(
            "Narxlar haqida aniq javob berish uchun operator ulanadi.",
            confidence=55,
            mocked=True,
        )
    return AutoReplyResult(
        "Rahmat, savolingizni qayd qildim. Operator tez orada javob beradi.",
        confidence=70,
        mocked=True,
    )


def _parse_json(text: str) -> AutoReplyResult | None:
    if not text or "{" not in text:
        return None
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
    except (ValueError, KeyError):
        return None
    reply = data.get("reply")
    conf = data.get("confidence")
    if not isinstance(reply, str) or not isinstance(conf, int | float):
        return None
    return AutoReplyResult(
        reply=str(reply).strip()[:2000],
        confidence=max(0, min(100, int(conf))),
        mocked=False,
    )


async def draft_reply(
    db: AsyncSession,
    *,
    conversation: Conversation,
    incoming: Message,
) -> AutoReplyResult:
    """Compose a draft reply for the given incoming message.

    The caller decides whether to actually send it (e.g. when confidence
    >= AutoReplyConfig.confidence_threshold).
    """
    if _is_mock_mode():
        return _mock_reply(incoming.body)

    brand = await db.get(Brand, conversation.brand_id) if conversation.brand_id else None
    history_rows = await _history(db, conversation.id, limit=6)
    rag = await _rag_context(db, brand_id=conversation.brand_id, query=incoming.body)

    template = _load_template()
    brand_name = brand.name if brand else "Brand"
    brand_voice = (brand.voice_tone if brand else None) or "Friendly, professional"
    brand_audience = (brand.target_audience if brand else None) or "General customers"
    brand_languages = ", ".join((brand.languages if brand else ["uz"]) or ["uz"])
    rendered = (
        template.replace("{brand_name}", brand_name)
        .replace("{brand_voice}", brand_voice)
        .replace("{brand_audience}", brand_audience)
        .replace("{brand_languages}", brand_languages)
        .replace("{rag_context}", rag)
        .replace("{history}", _format_history(history_rows))
        .replace("{incoming}", incoming.body.strip()[:1500])
    )

    try:
        resp = await ai_service.complete(
            db, system=SYSTEM_GUARDRAILS, user=rendered, max_tokens=400
        )
    except Exception as exc:
        logger.warning("Auto-reply AI call failed (%s) — using mock fallback", exc)
        return _mock_reply(incoming.body)

    parsed = _parse_json(resp.text)
    if parsed is None:
        return _mock_reply(incoming.body)
    return parsed


__all__ = ["AutoReplyResult", "draft_reply"]
