from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SocialAccountOut(BaseModel):
    id: UUID
    brand_id: UUID
    provider: str
    external_id: str
    external_handle: str | None
    external_name: str | None
    chat_type: str | None
    is_active: bool
    last_published_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TelegramLinkRequest(BaseModel):
    brand_id: UUID
    chat: str = Field(min_length=1, max_length=100, description="@username or numeric chat_id")


class TelegramTestRequest(BaseModel):
    account_id: UUID
    text: str = Field(min_length=1, max_length=2000)


class TelegramSendResult(BaseModel):
    message_id: int
    chat_id: int | str
    sent_text: str
    mocked: bool


class TelegramBotInfo(BaseModel):
    username: str | None
    first_name: str | None
    bot_id: int | None
    can_join_groups: bool | None
    mocked: bool
