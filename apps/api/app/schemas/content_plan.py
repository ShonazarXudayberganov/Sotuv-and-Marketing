from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ContentPlanItemOut(BaseModel):
    id: UUID
    brand_id: UUID
    post_id: UUID | None
    platform: str
    title: str
    idea: str
    goal: str | None
    cta: str | None
    status: str
    planned_at: datetime | None
    source: str
    sort_order: int
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ContentPlanItemCreate(BaseModel):
    brand_id: UUID
    platform: str = Field(default="instagram", min_length=2, max_length=30)
    title: str = Field(min_length=1, max_length=200)
    idea: str = Field(min_length=1, max_length=5000)
    goal: str | None = Field(default=None, max_length=500)
    cta: str | None = Field(default=None, max_length=300)
    status: str = Field(default="idea", min_length=2, max_length=20)
    planned_at: datetime | None = None
    source: str = Field(default="manual", min_length=2, max_length=30)
    sort_order: int = 0
    metadata: dict[str, Any] | None = None


class ContentPlanItemUpdate(BaseModel):
    platform: str | None = Field(default=None, min_length=2, max_length=30)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    idea: str | None = Field(default=None, min_length=1, max_length=5000)
    goal: str | None = Field(default=None, max_length=500)
    cta: str | None = Field(default=None, max_length=300)
    status: str | None = Field(default=None, min_length=2, max_length=20)
    planned_at: datetime | None = None
    sort_order: int | None = None
    metadata: dict[str, Any] | None = None


class ContentPlanImportTextRequest(BaseModel):
    brand_id: UUID
    platform: str = Field(default="instagram", min_length=2, max_length=30)
    topic: str | None = Field(default=None, max_length=1000)
    text: str = Field(min_length=2, max_length=30000)
    start_date: date


class ContentPlanCreatePostRequest(BaseModel):
    social_account_ids: list[UUID] = Field(min_length=1)
    scheduled_at: datetime | None = None


class ContentPlanImportResult(BaseModel):
    items: list[ContentPlanItemOut]
