from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.core.knowledge_sections import DEFAULT_KNOWLEDGE_SECTION, validate_knowledge_section
from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import (
    AIChatImportRequest,
    DocumentOut,
    InstagramImportRequest,
    KnowledgeSectionOut,
    KnowledgeStats,
    SearchHit,
    SearchRequest,
    SearchResponse,
    TextDocumentCreate,
    WebsiteImportRequest,
)
from app.services import audit_service, knowledge_service

router = APIRouter()


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    brand_id: UUID | None = None,
    section: str | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[KnowledgeDocument]:
    try:
        normalized_section = validate_knowledge_section(section) if section else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await knowledge_service.list_documents(db, brand_id=brand_id, section=normalized_section)


@router.get("/sections", response_model=list[KnowledgeSectionOut])
async def list_sections(
    brand_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[KnowledgeSectionOut]:
    rows = await knowledge_service.section_progress(db, brand_id=brand_id)
    return [KnowledgeSectionOut(**row) for row in rows]


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
            section=payload.section,
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
        metadata={
            "brand_id": str(payload.brand_id),
            "title": payload.title,
            "section": payload.section,
            "type": "text",
        },
        request=request,
    )
    await db.commit()
    return doc


@router.post("/import/website", response_model=DocumentOut, status_code=201)
async def import_website_document(
    payload: WebsiteImportRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> KnowledgeDocument:
    try:
        doc = await knowledge_service.import_website(
            db,
            brand_id=payload.brand_id,
            url=str(payload.url),
            title=payload.title,
            section=payload.section,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="knowledge.import_website",
        resource_type="document",
        resource_id=str(doc.id),
        metadata={
            "brand_id": str(payload.brand_id),
            "section": payload.section,
            "url": str(payload.url),
        },
        request=request,
    )
    await db.commit()
    return doc


@router.post("/import/instagram", response_model=DocumentOut, status_code=201)
async def import_instagram_document(
    payload: InstagramImportRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> KnowledgeDocument:
    try:
        doc = await knowledge_service.import_instagram(
            db,
            brand_id=payload.brand_id,
            account_id=payload.account_id,
            title=payload.title,
            section=payload.section,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="knowledge.import_instagram",
        resource_type="document",
        resource_id=str(doc.id),
        metadata={
            "brand_id": str(payload.brand_id),
            "section": payload.section,
            "account_id": str(payload.account_id) if payload.account_id else None,
        },
        request=request,
    )
    await db.commit()
    return doc


@router.post("/import/ai-chat", response_model=DocumentOut, status_code=201)
async def import_ai_chat_document(
    payload: AIChatImportRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> KnowledgeDocument:
    try:
        doc = await knowledge_service.import_ai_chat(
            db,
            brand_id=payload.brand_id,
            prompt=payload.prompt,
            title=payload.title,
            section=payload.section,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="knowledge.import_ai_chat",
        resource_type="document",
        resource_id=str(doc.id),
        metadata={"brand_id": str(payload.brand_id), "section": payload.section},
        request=request,
    )
    await db.commit()
    return doc


@router.post("/documents/file", response_model=DocumentOut, status_code=201)
async def upload_file_document(
    request: Request,
    brand_id: UUID = Form(...),
    title: str = Form(...),
    section: str = Form(DEFAULT_KNOWLEDGE_SECTION),
    file: UploadFile = File(...),
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> KnowledgeDocument:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    text = knowledge_service.extract_text_from_upload(file.filename or "", contents)
    try:
        normalized_section = validate_knowledge_section(section)
        doc = await knowledge_service.ingest_document(
            db,
            brand_id=brand_id,
            title=title,
            section=normalized_section,
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
            "section": normalized_section,
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
