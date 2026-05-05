"""Knowledge base lifecycle: ingest documents, embed chunks, run RAG search."""

from __future__ import annotations

import io
import logging
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any
from uuid import UUID

import httpx
from pypdf import PdfReader
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chunker import chunk_text
from app.core.knowledge_sections import KNOWLEDGE_SECTIONS, validate_knowledge_section
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.smm import Brand, BrandSocialAccount
from app.services import ai_service, embeddings_service, meta_service

logger = logging.getLogger(__name__)
WEBSITE_TIMEOUT_SECONDS = 15
MAX_WEBSITE_BYTES = 1_000_000


class _ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []
        self.title: str | None = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "div", "li", "br", "section", "article", "h1", "h2", "h3"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "li", "section", "article", "h1", "h2", "h3"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text or self._skip_depth:
            return
        if self._in_title:
            self.title = text if self.title is None else f"{self.title} {text}"
        self._parts.append(text)

    def readable_text(self) -> str:
        raw = " ".join(self._parts)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r"\n\s*\n\s*", "\n\n", raw)
        return raw.strip()


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


async def fetch_website_text(url: str) -> tuple[str, str | None]:
    async with httpx.AsyncClient(
        timeout=WEBSITE_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": "NEXUS-AI-KnowledgeBot/1.0"},
    ) as http:
        resp = await http.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            raise ValueError("URL did not return HTML or plain text")
        payload = resp.content[:MAX_WEBSITE_BYTES]
    if "text/plain" in content_type:
        return payload.decode("utf-8", errors="ignore").strip(), None

    parser = _ReadableHTMLParser()
    parser.feed(payload.decode("utf-8", errors="ignore"))
    return parser.readable_text(), parser.title


async def ingest_document(
    db: AsyncSession,
    *,
    brand_id: UUID,
    title: str,
    section: str,
    raw_text: str,
    source_type: str,
    source_url: str | None,
    user_id: UUID,
) -> KnowledgeDocument:
    """Persist the document, chunk it, embed each chunk, store vectors."""
    if not raw_text.strip():
        raise ValueError("Document text is empty")
    section = validate_knowledge_section(section)

    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")

    doc = KnowledgeDocument(
        brand_id=brand_id,
        title=title,
        section=section,
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


async def import_website(
    db: AsyncSession,
    *,
    brand_id: UUID,
    url: str,
    title: str | None,
    section: str,
    user_id: UUID,
) -> KnowledgeDocument:
    try:
        text_content, page_title = await fetch_website_text(url)
    except httpx.HTTPError as exc:
        raise ValueError(f"Website import failed: {exc}") from exc
    final_title = title or page_title or url
    return await ingest_document(
        db,
        brand_id=brand_id,
        title=final_title[:200],
        section=section,
        raw_text=text_content,
        source_type="website",
        source_url=url,
        user_id=user_id,
    )


def _media_caption_lines(media: dict[str, Any]) -> list[str]:
    raw_rows = media.get("data")
    rows = raw_rows if isinstance(raw_rows, list) else []
    lines: list[str] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        caption = str(item.get("caption") or "").strip()
        if not caption:
            continue
        stats = []
        if item.get("like_count") is not None:
            stats.append(f"likes={item['like_count']}")
        if item.get("comments_count") is not None:
            stats.append(f"comments={item['comments_count']}")
        meta = f" ({', '.join(stats)})" if stats else ""
        lines.append(f"- {caption}{meta}")
    return lines


async def import_instagram(
    db: AsyncSession,
    *,
    brand_id: UUID,
    account_id: UUID | None,
    title: str | None,
    section: str,
    user_id: UUID,
) -> KnowledgeDocument:
    stmt = select(BrandSocialAccount).where(
        BrandSocialAccount.brand_id == brand_id,
        BrandSocialAccount.provider == "instagram",
        BrandSocialAccount.is_active.is_(True),
    )
    if account_id is not None:
        stmt = stmt.where(BrandSocialAccount.id == account_id)
    stmt = stmt.order_by(BrandSocialAccount.created_at.desc()).limit(1)
    account = (await db.execute(stmt)).scalars().first()
    if account is None:
        raise ValueError("Instagram account not linked")

    page_token = (account.metadata_ or {}).get("page_token")
    try:
        snapshot = await meta_service.get_instagram_profile_snapshot(
            db,
            ig_user_id=account.external_id,
            page_token=str(page_token) if page_token else None,
        )
    except meta_service.MetaError as exc:
        raise ValueError(f"Instagram import failed: {exc}") from exc
    username = str(snapshot.get("username") or account.external_handle or account.external_id)
    lines = [
        f"Instagram account: @{username}",
        f"Name: {snapshot.get('name') or account.external_name or '—'}",
    ]
    if snapshot.get("biography"):
        lines.append(f"Bio: {snapshot['biography']}")
    if snapshot.get("followers_count") is not None:
        lines.append(f"Followers: {snapshot['followers_count']}")
    if snapshot.get("media_count") is not None:
        lines.append(f"Media count: {snapshot['media_count']}")
    captions = _media_caption_lines(snapshot.get("media") or {})
    if captions:
        lines.append("\nRecent captions:")
        lines.extend(captions)

    return await ingest_document(
        db,
        brand_id=brand_id,
        title=(title or f"Instagram @{username}")[:200],
        section=section,
        raw_text="\n".join(lines),
        source_type="instagram",
        source_url=f"https://instagram.com/{username}",
        user_id=user_id,
    )


async def import_ai_chat(
    db: AsyncSession,
    *,
    brand_id: UUID,
    prompt: str,
    title: str | None,
    section: str,
    user_id: UUID,
) -> KnowledgeDocument:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")
    system = (
        "You create factual brand knowledge base notes for a social media AI. "
        "Do not write an ad or a social post. Convert the user's notes into concise, "
        "structured facts with headings and bullet points. Preserve exact prices, "
        "names, hours, limitations and policies when provided."
    )
    user = (
        f"Brand: {brand.name}\n"
        f"Industry: {brand.industry or 'unknown'}\n"
        f"Section: {section}\n\n"
        f"User notes:\n{prompt}"
    )
    try:
        result = await ai_service.complete(db, system=system, user=user, max_tokens=900)
    except ai_service.AIError as exc:
        raise ValueError(f"AI chat import failed: {exc}") from exc
    return await ingest_document(
        db,
        brand_id=brand_id,
        title=(title or f"AI chat import — {brand.name}")[:200],
        section=section,
        raw_text=result.text,
        source_type="ai_chat",
        source_url=None,
        user_id=user_id,
    )


async def list_documents(
    db: AsyncSession, *, brand_id: UUID | None = None, section: str | None = None
) -> list[KnowledgeDocument]:
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    if brand_id is not None:
        stmt = stmt.where(KnowledgeDocument.brand_id == brand_id)
    if section is not None:
        stmt = stmt.where(KnowledgeDocument.section == validate_knowledge_section(section))
    return list((await db.execute(stmt)).scalars())


async def section_progress(
    db: AsyncSession, *, brand_id: UUID | None = None
) -> list[dict[str, object]]:
    where = "WHERE d.brand_id = :brand_id" if brand_id is not None else ""
    rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    d.section,
                    COUNT(d.id) AS document_count,
                    COUNT(d.id) FILTER (WHERE d.embed_status = 'ready') AS ready_count,
                    COALESCE(SUM(d.chunk_count), 0) AS chunk_count
                FROM knowledge_documents d
                {where}
                GROUP BY d.section
                """
            ),
            {"brand_id": brand_id} if brand_id is not None else {},
        )
    ).mappings()
    by_key = {row["section"]: row for row in rows}
    progress: list[dict[str, object]] = []
    for section in KNOWLEDGE_SECTIONS:
        row = by_key.get(section["key"])
        document_count = int(row["document_count"]) if row else 0
        ready_count = int(row["ready_count"]) if row else 0
        chunk_count = int(row["chunk_count"]) if row else 0
        progress.append(
            {
                **section,
                "document_count": document_count,
                "ready_count": ready_count,
                "chunk_count": chunk_count,
                "completed": ready_count > 0,
            }
        )
    return progress


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
    sections = await section_progress(db, brand_id=brand_id)
    return {
        "documents": int(docs),
        "chunks": int(chunks),
        "sections_total": len(sections),
        "sections_completed": sum(1 for section in sections if section["completed"]),
    }


__all__ = [
    "delete_document",
    "extract_text_from_upload",
    "fetch_website_text",
    "import_ai_chat",
    "import_instagram",
    "import_website",
    "ingest_document",
    "list_documents",
    "search",
    "section_progress",
    "stats",
]


# Helper used by tests to introspect timing.
def now_iso() -> str:
    return datetime.now(UTC).isoformat()
