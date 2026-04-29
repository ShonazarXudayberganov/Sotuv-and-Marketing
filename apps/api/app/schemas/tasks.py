from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TaskStatus = Literal["new", "in_progress", "review", "done", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "critical"]


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None
    department_id: UUID | None
    related_type: str | None
    related_id: str | None
    starts_at: datetime | None
    due_at: datetime | None
    estimated_hours: int | None
    created_by: UUID
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    status: TaskStatus = "new"
    priority: TaskPriority = "medium"
    assignee_id: UUID | None = None
    department_id: UUID | None = None
    related_type: str | None = None
    related_id: str | None = None
    starts_at: datetime | None = None
    due_at: datetime | None = None
    estimated_hours: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: UUID | None = None
    department_id: UUID | None = None
    starts_at: datetime | None = None
    due_at: datetime | None = None
    estimated_hours: int | None = None


class TwoFactorSetupOut(BaseModel):
    secret: str
    qr_data_url: str
    backup_codes: list[str]


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    scopes: list[str] = Field(default_factory=list)
    rate_limit_per_minute: int = 60
    expires_in_days: int | None = None


class ApiKeyOut(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    rate_limit_per_minute: int
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreated(ApiKeyOut):
    plaintext_key: str
