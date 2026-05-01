from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PublicationOut(BaseModel):
    id: UUID
    post_id: UUID
    social_account_id: UUID
    provider: str
    status: str
    attempts: int
    next_retry_at: datetime | None
    external_post_id: str | None
    last_error: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    id: UUID
    brand_id: UUID
    draft_id: UUID | None
    title: str | None
    body: str
    media_urls: list[str] | None
    status: str
    scheduled_at: datetime | None
    published_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostDetailOut(PostOut):
    publications: list[PublicationOut]


class PostCreateRequest(BaseModel):
    brand_id: UUID
    body: str = Field(min_length=1, max_length=10000)
    title: str | None = Field(default=None, max_length=200)
    media_urls: list[str] | None = None
    social_account_ids: list[UUID] = Field(min_length=1)
    scheduled_at: datetime | None = None
    draft_id: UUID | None = None


class PostReschedule(BaseModel):
    scheduled_at: datetime | None = None


class PostStats(BaseModel):
    total: int
    by_status: dict[str, int]


class CalendarDay(BaseModel):
    date: str  # YYYY-MM-DD (UTC)
    posts: list[PostOut]


class CalendarOut(BaseModel):
    start: str
    end: str
    days: list[CalendarDay]
