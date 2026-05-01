from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

PLATFORMS = ("telegram", "instagram", "facebook", "youtube", "generic")


class GeneratePostRequest(BaseModel):
    brand_id: UUID
    platform: str = Field(min_length=2, max_length=30)
    user_goal: str = Field(min_length=2, max_length=2000)
    language: str = Field(default="uz", min_length=2, max_length=10)
    title: str | None = Field(default=None, max_length=200)
    use_cache: bool = True


class DraftOut(BaseModel):
    id: UUID
    brand_id: UUID
    platform: str
    title: str | None
    body: str
    user_goal: str | None
    language: str
    provider: str | None
    model: str | None
    tokens_used: int
    rag_chunk_ids: list[str] | None
    is_starred: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DraftPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    body: str | None = Field(default=None, max_length=10000)


class AIUsageOut(BaseModel):
    period: str
    tokens_used: int
    tokens_cap: int


class ContentStats(BaseModel):
    drafts_total: int
    drafts_starred: int
    by_platform: dict[str, int]
