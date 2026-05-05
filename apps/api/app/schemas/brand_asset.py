from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BrandAssetOut(BaseModel):
    id: UUID
    brand_id: UUID
    asset_type: str
    name: str
    file_url: str | None
    content_type: str | None
    file_size: int
    metadata: dict[str, Any] | None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class BrandAssetCreate(BaseModel):
    brand_id: UUID
    asset_type: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=1, max_length=160)
    file_url: str | None = None
    content_type: str | None = Field(default=None, max_length=120)
    file_size: int = Field(default=0, ge=0)
    metadata: dict[str, Any] | None = None
    is_primary: bool = False


class BrandAssetUpdate(BaseModel):
    asset_type: str | None = Field(default=None, min_length=2, max_length=30)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    file_url: str | None = None
    content_type: str | None = Field(default=None, max_length=120)
    file_size: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] | None = None
    is_primary: bool | None = None
