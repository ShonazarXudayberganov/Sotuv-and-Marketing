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


# ─────────── Deals / Pipelines ───────────


class StageOut(BaseModel):
    id: UUID
    pipeline_id: UUID
    name: str
    slug: str
    sort_order: int
    default_probability: int
    is_won: bool
    is_lost: bool
    color: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineOut(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    is_default: bool
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineWithStages(PipelineOut):
    stages: list[StageOut]


class DealOut(BaseModel):
    id: UUID
    title: str
    contact_id: UUID | None
    pipeline_id: UUID
    stage_id: UUID
    amount: int
    currency: str
    probability: int
    status: str
    is_won: bool
    expected_close_at: datetime | None
    closed_at: datetime | None
    department_id: UUID | None
    assignee_id: UUID | None
    notes: str | None
    tags: list[str] | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DealCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    contact_id: UUID | None = None
    pipeline_id: UUID | None = None
    stage_id: UUID | None = None
    amount: int = Field(default=0, ge=0)
    currency: str = Field(default="UZS", min_length=3, max_length=3)
    expected_close_at: datetime | None = None
    assignee_id: UUID | None = None
    department_id: UUID | None = None
    notes: str | None = None
    tags: list[str] | None = None


class DealPatch(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    contact_id: UUID | None = None
    stage_id: UUID | None = None
    amount: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    probability: int | None = Field(default=None, ge=0, le=100)
    expected_close_at: datetime | None = None
    assignee_id: UUID | None = None
    department_id: UUID | None = None
    notes: str | None = None
    tags: list[str] | None = None
    sort_order: int | None = None


class ForecastOut(BaseModel):
    open_count: int
    open_amount: int
    weighted_amount: int
    by_stage: dict[str, dict[str, int]]


class DealStats(BaseModel):
    total: int
    by_status: dict[str, int]
    won_amount: int
    lost_amount: int
    win_rate: float
