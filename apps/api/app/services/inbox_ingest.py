"""Inbound-message ingestion: turn provider payloads into Inbox messages.

Sprint 2.3 ships Telegram + a deterministic mock-seed for dev. Meta and
website-widget hooks join later. After persisting the inbound message we
optionally trigger AI auto-reply (when the per-tenant AutoReplyConfig is
enabled and confidence clears the threshold).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inbox import AutoReplyConfig, Conversation, Message
from app.services import auto_reply_service, inbox_service

logger = logging.getLogger(__name__)


def _quiet_hour(now: datetime, cfg: AutoReplyConfig) -> bool:
    if cfg.quiet_hours_start is None or cfg.quiet_hours_end is None:
        return False
    h = now.astimezone(UTC).hour
    s, e = cfg.quiet_hours_start, cfg.quiet_hours_end
    if s <= e:
        return s <= h < e
    return h >= s or h < e


async def ingest_inbound(
    db: AsyncSession,
    *,
    channel: str,
    external_id: str,
    body: str,
    title: str | None = None,
    contact_id: UUID | None = None,
    brand_id: UUID | None = None,
    occurred_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
    auto_reply: bool = True,
) -> tuple[Conversation, Message, Message | None]:
    """Persist an inbound message; return the (conversation, msg, auto_reply_msg)."""
    conversation = await inbox_service.get_or_create_conversation(
        db,
        channel=channel,
        external_id=external_id,
        title=title,
        contact_id=contact_id,
        brand_id=brand_id,
    )
    if conversation.brand_id is None and brand_id is not None:
        conversation.brand_id = brand_id

    msg = await inbox_service.add_message(
        db,
        conversation=conversation,
        direction="in",
        body=body,
        sent_by="contact",
        occurred_at=occurred_at,
        metadata=metadata,
    )

    from app.services import webhook_service

    await webhook_service.fire_event(
        db,
        event="inbox.message_in",
        payload={
            "conversation_id": str(conversation.id),
            "channel": conversation.channel,
            "external_id": conversation.external_id,
            "body": body[:500],
        },
    )

    auto_msg: Message | None = None
    if auto_reply:
        auto_msg = await _maybe_auto_reply(db, conversation=conversation, incoming=msg)
    return conversation, msg, auto_msg


async def _maybe_auto_reply(
    db: AsyncSession,
    *,
    conversation: Conversation,
    incoming: Message,
) -> Message | None:
    cfg = await inbox_service.get_auto_reply_config(db)
    if not cfg.is_enabled:
        return None
    enabled_channels = cfg.channels_enabled or []
    if enabled_channels and conversation.channel not in enabled_channels:
        return None
    if _quiet_hour(datetime.now(UTC), cfg):
        return None

    # Pick a brand fallback for context if the conversation has none yet.
    if conversation.brand_id is None and cfg.default_brand_id is not None:
        conversation.brand_id = cfg.default_brand_id

    draft = await auto_reply_service.draft_reply(
        db, conversation=conversation, incoming=incoming
    )
    if draft.confidence < cfg.confidence_threshold:
        logger.info(
            "Inbox auto-reply skipped: confidence %s < threshold %s",
            draft.confidence,
            cfg.confidence_threshold,
        )
        return None
    # Send via the right provider; persist the outbound message either way.
    try:
        return await inbox_service.send_outbound(
            db,
            conversation=conversation,
            body=draft.reply,
            sent_by_user_id=conversation.assignee_id or _system_user_id(),
            is_auto_reply=True,
            confidence=draft.confidence,
        )
    except RuntimeError as exc:
        logger.warning("Auto-reply send failed: %s", exc)
        return None


_SYSTEM_USER = UUID("00000000-0000-0000-0000-000000000000")


def _system_user_id() -> UUID:
    return _SYSTEM_USER


# ─────────── Provider adapters ───────────


def telegram_message_payload(update: dict[str, Any]) -> dict[str, Any] | None:
    """Pull a clean (chat, body, sender) tuple out of a Telegram update."""
    msg = update.get("message") or update.get("edited_message") or update.get(
        "channel_post"
    )
    if not isinstance(msg, dict):
        return None
    chat = msg.get("chat") or {}
    body = msg.get("text") or msg.get("caption")
    if not body:
        return None
    chat_id = chat.get("id")
    if chat_id is None:
        return None
    title = chat.get("title") or chat.get("username") or chat.get("first_name")
    sender = msg.get("from") or {}
    occurred_ts = msg.get("date")
    occurred = (
        datetime.fromtimestamp(occurred_ts, tz=UTC)
        if isinstance(occurred_ts, int)
        else datetime.now(UTC)
    )
    return {
        "external_id": str(chat_id),
        "body": str(body),
        "title": title,
        "occurred_at": occurred,
        "metadata": {"raw": msg, "sender": sender},
    }


# ─────────── Mock seed ───────────


MOCK_SCRIPT: tuple[dict[str, Any], ...] = (
    {
        "external_id": "mock_user_001",
        "title": "Mock Mijoz #1",
        "body": "Salom! Bugun ish vaqtingiz qachon?",
    },
    {
        "external_id": "mock_user_002",
        "title": "Mock Mijoz #2",
        "body": "Manikur narxi qancha?",
    },
    {
        "external_id": "mock_user_001",
        "title": "Mock Mijoz #1",
        "body": "Yana bir savol — yetkazib berasizmi?",
    },
)


async def seed_mock_conversations(
    db: AsyncSession, *, brand_id: UUID | None = None, channel: str = "telegram"
) -> int:
    """Insert a deterministic batch of inbound messages for demo purposes."""
    inserted = 0
    for entry in MOCK_SCRIPT:
        await ingest_inbound(
            db,
            channel=channel,
            external_id=str(entry["external_id"]),
            body=str(entry["body"]),
            title=str(entry["title"]),
            brand_id=brand_id,
            auto_reply=False,
        )
        inserted += 1
    return inserted


__all__ = [
    "MOCK_SCRIPT",
    "ingest_inbound",
    "seed_mock_conversations",
    "telegram_message_payload",
]
