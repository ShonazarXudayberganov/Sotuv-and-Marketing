from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: UUID
    brand_id: UUID
    title: str
    source_type: str
    source_url: str | None
    chunk_count: int
    embed_status: str
    embed_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TextDocumentCreate(BaseModel):
    brand_id: UUID
    title: str = Field(min_length=2, max_length=200)
    text: str = Field(min_length=1)
    source_url: str | None = Field(default=None, max_length=500)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    brand_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=25)


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    brand_id: str
    position: int
    content: str
    token_count: int
    similarity: float


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]


class KnowledgeStats(BaseModel):
    documents: int
    chunks: int
