from __future__ import annotations

from datetime import datetime
from typing import Literal
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


class GenerateContentRequest(GeneratePostRequest):
    variants: int = Field(default=3, ge=1, le=5)


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


class GenerateContentResponse(BaseModel):
    drafts: list[DraftOut]


class ImproveContentRequest(BaseModel):
    draft_id: UUID
    instruction: str = Field(min_length=2, max_length=1000)
    selected_text: str | None = Field(default=None, max_length=5000)


class AIChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AIChatRequest(BaseModel):
    brand_id: UUID
    message: str = Field(min_length=2, max_length=4000)
    draft_id: UUID | None = None
    history: list[AIChatMessage] = Field(default_factory=list, max_length=10)
    language: str = Field(default="uz", min_length=2, max_length=10)


class AITextResponse(BaseModel):
    text: str
    provider: str | None
    model: str | None
    tokens_used: int
    rag_chunk_ids: list[str] | None = None


class GenerateHashtagsRequest(BaseModel):
    brand_id: UUID
    platform: str = Field(default="instagram", min_length=2, max_length=30)
    topic: str = Field(min_length=2, max_length=1000)
    language: str = Field(default="uz", min_length=2, max_length=10)
    count: int = Field(default=30, ge=1, le=30)


class HashtagResponse(AITextResponse):
    hashtags: list[str]


class GenerateReelsScriptRequest(BaseModel):
    brand_id: UUID
    topic: str = Field(min_length=2, max_length=1000)
    language: str = Field(default="uz", min_length=2, max_length=10)
    duration_seconds: int = Field(default=30, ge=10, le=120)


class GeneratePlanRequest(BaseModel):
    brand_id: UUID
    platform: str = Field(default="instagram", min_length=2, max_length=30)
    topic: str = Field(min_length=2, max_length=1000)
    language: str = Field(default="uz", min_length=2, max_length=10)
    days: int = Field(default=30, ge=7, le=60)


class AIUsageOut(BaseModel):
    period: str
    tokens_used: int
    tokens_cap: int


class ContentStats(BaseModel):
    drafts_total: int
    drafts_starred: int
    by_platform: dict[str, int]
