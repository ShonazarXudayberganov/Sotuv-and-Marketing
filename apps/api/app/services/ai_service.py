"""AI provider abstraction.

Primary: Anthropic Claude (Messages API).
Backup: OpenAI GPT-4o (Chat Completions API).
Mock fallback: deterministic text — used when ``AI_MOCK=true`` or neither
provider has credentials configured.

The service tracks token usage per tenant (``AiUsage``) and refuses calls
once the monthly cap is reached. A 24h-style cache key is computed by the
caller (``content_service``) — the cache itself lives in the DB on
``content_drafts.cache_key``.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import AiUsage
from app.services.integration_service import get_credentials

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-opus-4-7"
ANTHROPIC_VERSION = "2023-06-01"

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-2024-11-20"

DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT = 60


class AIError(RuntimeError):
    """Raised when no AI provider can satisfy the request."""


class AICapExceededError(AIError):
    """Raised when the tenant has hit its monthly token cap."""


@dataclass
class AIResponse:
    text: str
    provider: str  # "anthropic" | "openai" | "mock"
    model: str
    tokens_in: int
    tokens_out: int

    @property
    def total_tokens(self) -> int:
        return self.tokens_in + self.tokens_out


def _is_mock_mode() -> bool:
    return os.getenv("AI_MOCK", "false").lower() in {"1", "true", "yes"}


def _current_period() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


# ─────────── Cap tracking ───────────


async def _get_or_create_usage(db: AsyncSession, period: str) -> AiUsage:
    row = (
        (await db.execute(select(AiUsage).where(AiUsage.period == period))).scalars().first()
    )
    if row is not None:
        return row
    row = AiUsage(period=period, tokens_used=0, tokens_cap=0)
    db.add(row)
    await db.flush()
    return row


async def _check_cap(db: AsyncSession) -> AiUsage:
    """Return the current period's row. Raise if cap is exhausted."""
    usage = await _get_or_create_usage(db, _current_period())
    cap = int(usage.tokens_cap or 0)
    used = int(usage.tokens_used or 0)
    if cap > 0 and used >= cap:
        raise AICapExceededError(
            f"Monthly AI token cap reached ({used}/{cap}). Upgrade plan or wait next period."
        )
    return usage


async def _record_usage(db: AsyncSession, tokens: int) -> None:
    usage = await _get_or_create_usage(db, _current_period())
    usage.tokens_used = int(usage.tokens_used or 0) + tokens
    await db.flush()


# ─────────── Provider implementations ───────────


async def _call_anthropic(
    api_key: str, system: str, user: str, *, max_tokens: int
) -> AIResponse:
    payload: dict[str, Any] = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as http:
        resp = await http.post(ANTHROPIC_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    blocks = data.get("content") or []
    text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
    usage = data.get("usage") or {}
    return AIResponse(
        text=text.strip(),
        provider="anthropic",
        model=str(data.get("model") or ANTHROPIC_MODEL),
        tokens_in=int(usage.get("input_tokens") or 0),
        tokens_out=int(usage.get("output_tokens") or 0),
    )


async def _call_openai(api_key: str, system: str, user: str, *, max_tokens: int) -> AIResponse:
    payload: dict[str, Any] = {
        "model": OPENAI_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as http:
        resp = await http.post(OPENAI_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    text = (message.get("content") or "").strip()
    usage = data.get("usage") or {}
    return AIResponse(
        text=text,
        provider="openai",
        model=str(data.get("model") or OPENAI_MODEL),
        tokens_in=int(usage.get("prompt_tokens") or 0),
        tokens_out=int(usage.get("completion_tokens") or 0),
    )


def _mock_complete(system: str, user: str) -> AIResponse:
    """Deterministic, somewhat readable output — keeps the UX testable."""
    seed = hashlib.sha256(f"{system}\n\n{user}".encode()).hexdigest()[:8]
    body = (
        "✨ NEXUS AI DEMO POST ✨\n\n"
        f"{user.strip()[:240]}\n\n"
        "Bu — sun'iy intellekt tomonidan tayyorlangan namuna kontent. "
        "Haqiqiy provayder ulansa, brendingiz uslubi va RAG ma'lumotidan "
        "to'liq foydalanib mukammal post yaratiladi.\n\n"
        f"#nexusai #demo #{seed}"
    )
    # Rough token estimate: ~4 chars/token
    tokens_in = max(1, len(system + user) // 4)
    tokens_out = max(1, len(body) // 4)
    return AIResponse(
        text=body,
        provider="mock",
        model="nexus-mock",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )


# ─────────── Public API ───────────


async def complete(
    db: AsyncSession,
    *,
    system: str,
    user: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> AIResponse:
    """Run the full multi-provider pipeline, recording token usage."""
    await _check_cap(db)

    if _is_mock_mode():
        out = _mock_complete(system, user)
        await _record_usage(db, out.total_tokens)
        return out

    # Try Claude first.
    anthropic_creds = await get_credentials(db, "anthropic")
    anthropic_key = (anthropic_creds or {}).get("api_key") if anthropic_creds else None
    if anthropic_key:
        try:
            out = await _call_anthropic(str(anthropic_key), system, user, max_tokens=max_tokens)
            await _record_usage(db, out.total_tokens)
            return out
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("Anthropic call failed (%s) — falling back to OpenAI", exc)

    # Fall back to OpenAI.
    openai_creds = await get_credentials(db, "openai")
    openai_key = (openai_creds or {}).get("api_key") if openai_creds else None
    if openai_key:
        try:
            out = await _call_openai(str(openai_key), system, user, max_tokens=max_tokens)
            await _record_usage(db, out.total_tokens)
            return out
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("OpenAI call failed (%s) — falling back to mock", exc)

    # Last resort: deterministic mock so the UX keeps working in dev.
    out = _mock_complete(system, user)
    await _record_usage(db, out.total_tokens)
    return out


async def get_usage_snapshot(db: AsyncSession) -> dict[str, int | str]:
    period = _current_period()
    usage = await _get_or_create_usage(db, period)
    return {
        "period": period,
        "tokens_used": int(usage.tokens_used or 0),
        "tokens_cap": int(usage.tokens_cap or 0),
    }


__all__ = [
    "AICapExceededError",
    "AIError",
    "AIResponse",
    "complete",
    "get_usage_snapshot",
]
