from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WebhookEndpointOut(BaseModel):
    id: UUID
    name: str
    direction: str
    url: str | None
    events: list[str] | None
    is_active: bool
    last_triggered_at: datetime | None
    last_status: int | None
    last_error: str | None
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookEndpointWithSecret(WebhookEndpointOut):
    secret: str


class WebhookEndpointCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    direction: str = Field(pattern="^(in|out)$")
    url: str | None = Field(default=None, max_length=500)
    events: list[str] | None = None


class WebhookDeliveryOut(BaseModel):
    id: UUID
    endpoint_id: UUID
    direction: str
    event: str | None
    status_code: int | None
    attempts: int
    succeeded: bool
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TestDeliveryRequest(BaseModel):
    event: str = Field(default="test.ping", min_length=2, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
