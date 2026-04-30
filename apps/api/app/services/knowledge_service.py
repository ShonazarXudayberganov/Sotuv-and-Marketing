"""Knowledge base lifecycle: ingest documents, embed chunks, run RAG search."""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pypdf import PdfReader
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chunker import chunk_text
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.smm import Brand
from app.services import embeddings_service

logger = logging.getLogger(__name__)


def extract_text_from_upload(filename: str, payload: bytes) -> str:
    """Best-effort text extraction. Supports PDF and plain UTF-8 text."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(payload))
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception as exc:
                logger.warning("PDF page extraction failed: %s", exc)
                continue
        return "\n\n".join(p for p in parts if p.strip())
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return payload.decode("utf-8", errors="ignore")


async def ingest_document(
    db: AsyncSession,
    *,
    brand_id: UUID,
    title: str,
    raw_text: str,
    source_type: str,
    source_url: str | None,
    user_id: UUID,
) -> KnowledgeDocument:
    """Persist the document, chunk it, embed each chunk, store vectors."""
    if not raw_text.strip():
        raise ValueError("Document text is empty")

    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")

    doc = KnowledgeDocument(
        brand_id=brand_id,
        title=title,
        source_type=source_type,
        source_url=source_url,
        raw_text=raw_text,
        embed_status="processing",
        chunk_count=0,
        created_by=user_id,
    )
    db.add(doc)
    await db.flush()

    chunks = chunk_text(raw_text)
    if not chunks:
        doc.embed_status = "empty"
        await db.flush()
        return doc

    try:
        embeddings = await embeddings_service.embed_texts(db, [c.content for c in chunks])
    except Exception as exc:
        doc.embed_status = "failed"
        doc.embed_error = str(exc)[:500]
        await db.flush()
        raise

    for chunk, vector in zip(chunks, embeddings, strict=False):
        db.add(
            KnowledgeChunk(
                document_id=doc.id,
                brand_id=brand_id,
                position=chunk.position,
                content=chunk.content,
                token_count=chunk.token_count,
                embedding=vector,
            )
        )

    doc.chunk_count = len(chunks)
    doc.embed_status = "ready"
    await db.flush()
    return doc


async def list_documents(
    db: AsyncSession, *, brand_id: UUID | None = None
) -> list[KnowledgeDocument]:
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    if brand_id is not None:
        stmt = stmt.where(KnowledgeDocument.brand_id == brand_id)
    return list((await db.execute(stmt)).scalars())


async def delete_document(db: AsyncSession, document_id: UUID) -> bool:
    doc = await db.get(KnowledgeDocument, document_id)
    if doc is None:
        return False
    await db.delete(doc)
    await db.flush()
    return True


async def search(
    db: AsyncSession,
    *,
    query: str,
    brand_id: UUID | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Cosine-similarity search against chunk embeddings."""
    if not query.strip():
        return []

    [vec] = await embeddings_service.embed_texts(db, [query])
    # pgvector + asyncpg expects the literal text format "[0.1,0.2,...]" for raw SQL casts
    vec_literal = "[" + ",".join(repr(float(x)) for x in vec) + "]"
    # pgvector cosine distance = 1 - cosine_similarity
    sql_clauses = [
        "SELECT c.id AS chunk_id, c.document_id, c.brand_id, c.position, "
        "c.content, c.token_count, "
        "1 - (c.embedding <=> CAST(:embedding AS vector)) AS similarity, "
        "d.title AS document_title "
        "FROM knowledge_chunks c "
        "JOIN knowledge_documents d ON d.id = c.document_id ",
    ]
    params: dict[str, Any] = {"embedding": vec_literal, "top_k": top_k}
    if brand_id is not None:
        sql_clauses.append("WHERE c.brand_id = :brand_id ")
        params["brand_id"] = brand_id
    sql_clauses.append("ORDER BY c.embedding <=> CAST(:embedding AS vector) ASC LIMIT :top_k")
    sql = "".join(sql_clauses)

    rows = await db.execute(text(sql), params)
    out: list[dict[str, Any]] = []
    for row in rows.mappings():
        out.append(
            {
                "chunk_id": str(row["chunk_id"]),
                "document_id": str(row["document_id"]),
                "document_title": row["document_title"],
                "brand_id": str(row["brand_id"]),
                "position": row["position"],
                "content": row["content"],
                "token_count": row["token_count"],
                "similarity": float(row["similarity"]),
            }
        )
    return out


async def stats(db: AsyncSession, *, brand_id: UUID | None = None) -> dict[str, int]:
    base = "SELECT COUNT(*) FROM knowledge_documents"
    base_chunks = "SELECT COUNT(*) FROM knowledge_chunks"
    if brand_id is not None:
        base += " WHERE brand_id = :b"
        base_chunks += " WHERE brand_id = :b"

    docs = (await db.execute(text(base), {"b": brand_id} if brand_id else {})).scalar_one()
    chunks = (await db.execute(text(base_chunks), {"b": brand_id} if brand_id else {})).scalar_one()
    return {"documents": int(docs), "chunks": int(chunks)}


__all__ = [
    "delete_document",
    "extract_text_from_upload",
    "ingest_document",
    "list_documents",
    "search",
    "stats",
]


# Helper used by tests to introspect timing.
def now_iso() -> str:
    return datetime.now(UTC).isoformat()
