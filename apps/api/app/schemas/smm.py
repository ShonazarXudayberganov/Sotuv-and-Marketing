from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BrandOut(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    industry: str | None
    logo_url: str | None
    primary_color: str | None
    voice_tone: str | None
    target_audience: str | None
    languages: list[str]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BrandCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    industry: str | None = Field(default=None, max_length=50)
    logo_url: str | None = Field(default=None, max_length=500)
    primary_color: str | None = Field(default=None, max_length=20)
    voice_tone: str | None = Field(default=None, max_length=500)
    target_audience: str | None = None
    languages: list[str] = Field(default_factory=lambda: ["uz"])
    is_default: bool = False


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    industry: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    voice_tone: str | None = None
    target_audience: str | None = None
    languages: list[str] | None = None
    is_active: bool | None = None


class IntegrationProvider(BaseModel):
    provider: str
    label: str
    category: str
    description: str
    secret_fields: list[str]
    display_field: str | None
    docs_url: str | None
    connected: bool
    is_active: bool
    label_custom: str | None
    display_value: str | None
    masked_values: dict[str, str]
    last_verified_at: str | None
    last_error: str | None
    updated_at: str | None


class IntegrationConnectRequest(BaseModel):
    label: str | None = Field(default=None, max_length=100)
    credentials: dict[str, Any]
    metadata: dict[str, Any] | None = None
