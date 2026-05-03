"""Inbox lifecycle: conversations, messages, mark-read, send out."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inbox import AutoReplyConfig, Conversation, Message
from app.models.smm import BrandSocialAccount
from app.services import meta_service, telegram_service
from app.services.meta_service import MetaError
from app.services.telegram_service import TelegramError

CHANNELS = ("telegram", "instagram", "facebook", "email", "web_widget")


async def list_conversations(
    db: AsyncSession,
    *,
    status: str | None = None,
    channel: str | None = None,
    contact_id: UUID | None = None,
    limit: int = 50,
) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .order_by(desc(Conversation.last_message_at), desc(Conversation.created_at))
        .limit(limit)
    )
    conds = []
    if status is not None:
        conds.append(Conversation.status == status)
    if channel is not None:
        conds.append(Conversation.channel == channel)
    if contact_id is not None:
        conds.append(Conversation.contact_id == contact_id)
    if conds:
        stmt = stmt.where(and_(*conds))
    return list((await db.execute(stmt)).scalars())


async def get_conversation(db: AsyncSession, cid: UUID) -> Conversation | None:
    return await db.get(Conversation, cid)


async def list_messages(db: AsyncSession, cid: UUID, *, limit: int = 100) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == cid)
        .order_by(asc(Message.occurred_at))
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars())


async def get_or_create_conversation(
    db: AsyncSession,
    *,
    channel: str,
    external_id: str,
    title: str | None = None,
    contact_id: UUID | None = None,
    brand_id: UUID | None = None,
) -> Conversation:
    stmt = select(Conversation).where(
        Conversation.channel == channel, Conversation.external_id == external_id
    )
    rec = (await db.execute(stmt)).scalars().first()
    if rec is not None:
        return rec
    rec = Conversation(
        channel=channel,
        external_id=external_id,
        title=title,
        contact_id=contact_id,
        brand_id=brand_id,
        status="open",
    )
    db.add(rec)
    await db.flush()
    return rec


async def add_message(
    db: AsyncSession,
    *,
    conversation: Conversation,
    direction: str,
    body: str,
    sent_by: str,
    sent_by_user_id: UUID | None = None,
    is_auto_reply: bool = False,
    confidence: int | None = None,
    external_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> Message:
    now = occurred_at or datetime.now(UTC)
    msg = Message(
        conversation_id=conversation.id,
        direction=direction,
        body=body,
        channel=conversation.channel,
        external_id=external_id,
        sent_by=sent_by,
        sent_by_user_id=sent_by_user_id,
        is_auto_reply=is_auto_reply,
        confidence=confidence,
        occurred_at=now,
        metadata_=metadata,
    )
    db.add(msg)
    conversation.last_message_at = now
    snippet = (body or "").strip().replace("\n", " ")
    conversation.snippet = snippet[:500] if snippet else conversation.snippet
    if direction == "in":
        conversation.last_inbound_at = now
        conversation.unread_count = (conversation.unread_count or 0) + 1
        if conversation.status == "closed":
            conversation.status = "open"
    else:
        conversation.last_outbound_at = now
    await db.flush()
    return msg


async def mark_read(db: AsyncSession, cid: UUID) -> Conversation | None:
    rec = await db.get(Conversation, cid)
    if rec is None:
        return None
    rec.unread_count = 0
    await db.flush()
    return rec


async def set_status(db: AsyncSession, cid: UUID, *, status: str) -> Conversation | None:
    if status not in {"open", "snoozed", "closed"}:
        raise ValueError("Invalid status")
    rec = await db.get(Conversation, cid)
    if rec is None:
        return None
    rec.status = status
    await db.flush()
    return rec


async def send_outbound(
    db: AsyncSession,
    *,
    conversation: Conversation,
    body: str,
    sent_by_user_id: UUID,
    is_auto_reply: bool = False,
    confidence: int | None = None,
) -> Message:
    """Persist + dispatch via the right provider."""
    body = body.strip()
    if not body:
        raise ValueError("Message body is empty")

    external_id: str | None = None
    if conversation.channel == "telegram":
        try:
            chat_id: int | str = conversation.external_id
            if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
                chat_id = int(chat_id)
            res = await telegram_service.send_message(db, chat_id=chat_id, text=body)
            external_id = str(res.get("message_id") or "") or None
        except TelegramError as exc:
            raise RuntimeError(f"Telegram send failed: {exc}") from exc
    elif conversation.channel == "facebook" and conversation.contact_id is not None:
        # Reuse the page token of the brand's FB account, if any
        page_token = await _resolve_meta_page_token(db, conversation.brand_id)
        if page_token:
            try:
                res = await meta_service.publish_facebook_post(
                    db,
                    page_id=conversation.external_id,
                    page_access_token=page_token,
                    message=body,
                )
                external_id = str(res.get("id") or "") or None
            except MetaError as exc:
                raise RuntimeError(f"Facebook send failed: {exc}") from exc
    # Other channels (instagram DM, email, web widget) — persist only
    return await add_message(
        db,
        conversation=conversation,
        direction="out",
        body=body,
        sent_by="ai" if is_auto_reply else "user",
        sent_by_user_id=sent_by_user_id,
        is_auto_reply=is_auto_reply,
        confidence=confidence,
        external_id=external_id,
    )


async def _resolve_meta_page_token(db: AsyncSession, brand_id: UUID | None) -> str | None:
    if brand_id is None:
        return None
    stmt = select(BrandSocialAccount).where(
        BrandSocialAccount.brand_id == brand_id,
        BrandSocialAccount.provider == "facebook",
    )
    rec = (await db.execute(stmt)).scalars().first()
    if rec is None:
        return None
    meta = rec.metadata_ or {}
    token = meta.get("page_token")
    return str(token) if token else None


# ─────────── AutoReplyConfig ───────────


async def get_auto_reply_config(db: AsyncSession) -> AutoReplyConfig:
    rec = (await db.execute(select(AutoReplyConfig))).scalars().first()
    if rec is None:
        rec = AutoReplyConfig(
            is_enabled=False,
            confidence_threshold=90,
            channels_enabled=["telegram"],
        )
        db.add(rec)
        await db.flush()
    return rec


async def update_auto_reply_config(db: AsyncSession, *, payload: dict[str, Any]) -> AutoReplyConfig:
    rec = await get_auto_reply_config(db)
    for field in (
        "is_enabled",
        "confidence_threshold",
        "quiet_hours_start",
        "quiet_hours_end",
        "default_brand_id",
        "fallback_text",
        "channels_enabled",
    ):
        if field in payload:
            setattr(rec, field, payload[field])
    await db.flush()
    return rec


async def stats(db: AsyncSession) -> dict[str, Any]:
    rows = list((await db.execute(select(Conversation))).scalars())
    by_status: dict[str, int] = {}
    by_channel: dict[str, int] = {}
    unread_total = 0
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        by_channel[r.channel] = by_channel.get(r.channel, 0) + 1
        unread_total += r.unread_count or 0
    msgs = (
        (await db.execute(select(Message).order_by(desc(Message.occurred_at)).limit(1)))
        .scalars()
        .first()
    )
    return {
        "total": len(rows),
        "by_status": by_status,
        "by_channel": by_channel,
        "unread": unread_total,
        "last_message_at": msgs.occurred_at.isoformat() if msgs else None,
    }


__all__ = [
    "CHANNELS",
    "add_message",
    "get_auto_reply_config",
    "get_conversation",
    "get_or_create_conversation",
    "list_conversations",
    "list_messages",
    "mark_read",
    "send_outbound",
    "set_status",
    "stats",
    "update_auto_reply_config",
]
