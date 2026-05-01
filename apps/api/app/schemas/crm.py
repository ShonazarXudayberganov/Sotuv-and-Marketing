from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

CONTACT_STATUSES = ("lead", "active", "customer", "lost", "archived")
ACTIVITY_KINDS = (
    "call_in",
    "call_out",
    "message_in",
    "message_out",
    "email",
    "note",
    "task",
    "meeting",
    "status_change",
)


class ContactOut(BaseModel):
    id: UUID
    full_name: str
    company_name: str | None
    phone: str | None
    email: str | None
    telegram_username: str | None
    instagram_username: str | None
    industry: str | None
    source: str | None
    status: str
    department_id: UUID | None
    assignee_id: UUID | None
    ai_score: int
    ai_score_reason: str | None
    ai_score_updated_at: datetime | None
    notes: str | None
    custom_fields: dict[str, Any] | None
    tags: list[str] | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    company_name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    telegram_username: str | None = Field(default=None, max_length=80)
    instagram_username: str | None = Field(default=None, max_length=80)
    industry: str | None = Field(default=None, max_length=50)
    source: str | None = Field(default=None, max_length=50)
    status: str = Field(default="lead")
    department_id: UUID | None = None
    assignee_id: UUID | None = None
    notes: str | None = None
    custom_fields: dict[str, Any] | None = None
    tags: list[str] | None = None


class ContactPatch(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    company_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    telegram_username: str | None = None
    instagram_username: str | None = None
    industry: str | None = None
    source: str | None = None
    status: str | None = None
    department_id: UUID | None = None
    assignee_id: UUID | None = None
    notes: str | None = None
    custom_fields: dict[str, Any] | None = None
    tags: list[str] | None = None


class ActivityOut(BaseModel):
    id: UUID
    contact_id: UUID
    kind: str
    title: str | None
    body: str | None
    direction: str | None
    channel: str | None
    duration_seconds: int | None
    occurred_at: datetime
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    kind: str = Field(min_length=2, max_length=30)
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None
    direction: str | None = Field(default=None, max_length=10)
    channel: str | None = Field(default=None, max_length=30)
    duration_seconds: int | None = None
    metadata: dict[str, Any] | None = None
    occurred_at: datetime | None = None


class ContactStats(BaseModel):
    total: int
    by_status: dict[str, int]
    hot_leads: int
    new_last_week: int


class AiScoreOut(BaseModel):
    score: int
    reason: str
