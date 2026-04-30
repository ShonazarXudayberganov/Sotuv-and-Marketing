from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import (
    DocumentOut,
    KnowledgeStats,
    SearchHit,
    SearchRequest,
    SearchResponse,
    TextDocumentCreate,
)
from app.services import audit_service, knowledge_service

router = APIRouter()


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    brand_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[KnowledgeDocument]:
    return await knowledge_service.list_documents(db, brand_id=brand_id)


@router.get("/stats", response_model=KnowledgeStats)
async def get_stats(
    brand_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> KnowledgeStats:
    counts = await knowledge_service.stats(db, brand_id=brand_id)
    return KnowledgeStats(**counts)


@router.post("/documents/text", response_model=DocumentOut, status_code=201)
async def upload_text_document(
    payload: TextDocumentCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> KnowledgeDocument:
    try:
        doc = await knowledge_service.ingest_document(
            db,
            brand_id=payload.brand_id,
            title=payload.title,
            raw_text=payload.text,
            source_type="text",
            source_url=payload.source_url,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="knowledge.upload",
        resource_type="document",
        resource_id=str(doc.id),
        metadata={"brand_id": str(payload.brand_id), "title": payload.title, "type": "text"},
        request=request,
    )
    await db.commit()
    return doc


@router.post("/documents/file", response_model=DocumentOut, status_code=201)
async def upload_file_document(
    request: Request,
    brand_id: UUID = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> KnowledgeDocument:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    text = knowledge_service.extract_text_from_upload(file.filename or "", contents)
    try:
        doc = await knowledge_service.ingest_document(
            db,
            brand_id=brand_id,
            title=title,
            raw_text=text,
            source_type="file",
            source_url=file.filename,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="knowledge.upload",
        resource_type="document",
        resource_id=str(doc.id),
        metadata={
            "brand_id": str(brand_id),
            "title": title,
            "type": "file",
            "filename": file.filename,
        },
        request=request,
    )
    await db.commit()
    return doc


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await knowledge_service.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="knowledge.delete",
        resource_type="document",
        resource_id=str(document_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    payload: SearchRequest,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> SearchResponse:
    hits = await knowledge_service.search(
        db, query=payload.query, brand_id=payload.brand_id, top_k=payload.top_k
    )
    return SearchResponse(query=payload.query, hits=[SearchHit(**h) for h in hits])
