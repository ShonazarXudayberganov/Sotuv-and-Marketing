from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

PostContentFormat = Literal["standard", "feed", "reels", "story"]


class PublicationEventOut(BaseModel):
    id: UUID
    publication_id: UUID
    post_id: UUID
    provider: str
    event_type: str
    status: str | None
    message: str | None
    metadata: dict[str, object] | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class PublicationOut(BaseModel):
    id: UUID
    post_id: UUID
    social_account_id: UUID
    provider: str
    status: str
    attempts: int
    next_retry_at: datetime | None
    last_attempt_at: datetime | None
    external_post_id: str | None
    remote_status: str | None
    last_checked_at: datetime | None
    permanent_failure: bool
    last_error: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    events: list[PublicationEventOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    id: UUID
    brand_id: UUID
    draft_id: UUID | None
    title: str | None
    body: str
    media_urls: list[str] | None
    content_format: PostContentFormat
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
    content_format: PostContentFormat | None = None
    social_account_ids: list[UUID] = Field(min_length=1)
    scheduled_at: datetime | None = None
    draft_id: UUID | None = None


class PostReschedule(BaseModel):
    scheduled_at: datetime | None = None


class PostReviewRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class PostApproveRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)
    scheduled_at: datetime | None = None


class PostRejectRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=1000)


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
