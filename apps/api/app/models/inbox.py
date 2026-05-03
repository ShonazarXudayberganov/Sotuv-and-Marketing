"""Inbox: omnichannel conversations + messages + per-tenant auto-reply config.

A Conversation aggregates messages from a single external party on a single
channel (telegram_user, instagram_dm, facebook_messenger, email, website_widget).
Messages flow both ways. AutoReplyConfig drives the AI auto-responder.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Conversation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "conversations"

    channel: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # telegram, instagram, facebook, email, web_widget
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    # Per-channel id (telegram chat_id, IG thread id, email From, widget session id)
    contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL"), index=True
    )
    brand_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(200))
    snippet: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open", index=True
    )  # open, snoozed, closed
    assignee_id: Mapped[UUID | None] = mapped_column()
    unread_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_inbound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_outbound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Message(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # in, out
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(120))
    sent_by: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user"
    )  # user, ai, contact
    sent_by_user_id: Mapped[UUID | None] = mapped_column()
    is_auto_reply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence: Mapped[int | None] = mapped_column(Integer)  # 0..100 for AI replies
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)


class AutoReplyConfig(Base, UUIDPKMixin, TimestampMixin):
    """Per-tenant config for the AI auto-replier (one row, upsert pattern)."""

    __tablename__ = "auto_reply_configs"

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence_threshold: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    quiet_hours_start: Mapped[int | None] = mapped_column(Integer)  # 0..23 UTC
    quiet_hours_end: Mapped[int | None] = mapped_column(Integer)
    default_brand_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL")
    )
    fallback_text: Mapped[str | None] = mapped_column(String(500))
    channels_enabled: Mapped[list[str] | None] = mapped_column(JSON)


__all__ = ["AutoReplyConfig", "Conversation", "Message"]
