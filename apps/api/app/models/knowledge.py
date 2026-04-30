"""Knowledge base models — per-brand document storage + pgvector embeddings.

Each brand can have multiple documents. Each document is chunked into
overlapping windows (~500 tokens) and embedded via OpenAI text-embedding-3-small
(1536 dimensions). Cosine similarity HNSW index serves RAG queries.
"""

from __future__ import annotations

from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin

EMBEDDING_DIM = 1536


class KnowledgeDocument(Base, UUIDPKMixin, TimestampMixin):
    """Source document — a file or pasted text the brand wants the AI to know."""

    __tablename__ = "knowledge_documents"

    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embed_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    embed_error: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[UUID] = mapped_column(nullable=False)


class KnowledgeChunk(Base, UUIDPKMixin, TimestampMixin):
    """A semantically-bounded slice of a document with its embedding."""

    __tablename__ = "knowledge_chunks"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    brand_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))


__all__ = ["EMBEDDING_DIM", "KnowledgeChunk", "KnowledgeDocument"]
