from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

CHANNELS = ("telegram", "instagram", "facebook", "email", "web_widget")


class ConversationOut(BaseModel):
    id: UUID
    channel: str
    external_id: str
    contact_id: UUID | None
    brand_id: UUID | None
    title: str | None
    snippet: str | None
    status: str
    assignee_id: UUID | None
    unread_count: int
    last_message_at: datetime | None
    last_inbound_at: datetime | None
    last_outbound_at: datetime | None
    tags: list[str] | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    direction: str
    body: str
    channel: str
    external_id: str | None
    sent_by: str
    sent_by_user_id: UUID | None
    is_auto_reply: bool
    confidence: int | None
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|snoozed|closed)$")


class IngestInboundRequest(BaseModel):
    channel: str = Field(min_length=2, max_length=30)
    external_id: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=4000)
    title: str | None = Field(default=None, max_length=200)
    contact_id: UUID | None = None
    brand_id: UUID | None = None
    metadata: dict[str, Any] | None = None
    auto_reply: bool = True


class AutoReplyConfigOut(BaseModel):
    is_enabled: bool
    confidence_threshold: int
    quiet_hours_start: int | None
    quiet_hours_end: int | None
    default_brand_id: UUID | None
    fallback_text: str | None
    channels_enabled: list[str] | None

    model_config = {"from_attributes": True}


class AutoReplyConfigPatch(BaseModel):
    is_enabled: bool | None = None
    confidence_threshold: int | None = Field(default=None, ge=0, le=100)
    quiet_hours_start: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=None, ge=0, le=23)
    default_brand_id: UUID | None = None
    fallback_text: str | None = Field(default=None, max_length=500)
    channels_enabled: list[str] | None = None


class AutoReplyDraft(BaseModel):
    reply: str
    confidence: int
    mocked: bool


class InboxStats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_channel: dict[str, int]
    unread: int
    last_message_at: str | None


class SeedResult(BaseModel):
    inserted: int
