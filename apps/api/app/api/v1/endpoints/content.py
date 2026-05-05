from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.smm import ContentDraft
from app.schemas.content import (
    AIChatRequest,
    AITextResponse,
    AIUsageOut,
    ContentStats,
    DraftOut,
    DraftPatch,
    GenerateContentRequest,
    GenerateContentResponse,
    GenerateHashtagsRequest,
    GeneratePlanRequest,
    GeneratePostRequest,
    GenerateReelsScriptRequest,
    HashtagResponse,
    ImproveContentRequest,
)
from app.services import ai_service, audit_service, content_service
from app.services.ai_service import AICapExceededError

router = APIRouter()


@router.post("/generate-post", response_model=DraftOut, status_code=201)
async def generate_post(
    payload: GeneratePostRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentDraft:
    try:
        draft = await content_service.generate_post(
            db,
            brand_id=payload.brand_id,
            platform=payload.platform,
            user_goal=payload.user_goal,
            language=payload.language,
            title=payload.title,
            use_cache=payload.use_cache,
            user_id=current.id,
        )
    except AICapExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.generate_post",
        resource_type="content_draft",
        resource_id=str(draft.id),
        metadata={
            "brand_id": str(payload.brand_id),
            "platform": payload.platform,
            "tokens": draft.tokens_used,
            "provider": draft.provider,
        },
        request=request,
    )
    draft_id = draft.id
    await db.commit()
    fresh = await db.get(ContentDraft, draft_id)
    if fresh is None:
        raise HTTPException(status_code=500, detail="Draft vanished after commit")
    return fresh


@router.post("/generate-content", response_model=GenerateContentResponse, status_code=201)
async def generate_content(
    payload: GenerateContentRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> GenerateContentResponse:
    try:
        drafts = await content_service.generate_variants(
            db,
            brand_id=payload.brand_id,
            platform=payload.platform,
            user_goal=payload.user_goal,
            language=payload.language,
            title=payload.title,
            variants=payload.variants,
            use_cache=payload.use_cache,
            user_id=current.id,
        )
    except AICapExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.generate_content",
        resource_type="content_draft",
        resource_id=str(drafts[0].id) if drafts else None,
        metadata={
            "brand_id": str(payload.brand_id),
            "platform": payload.platform,
            "variants": len(drafts),
            "tokens": sum(int(d.tokens_used or 0) for d in drafts),
        },
        request=request,
    )
    draft_ids = [d.id for d in drafts]
    await db.commit()
    fresh: list[ContentDraft] = []
    for draft_id in draft_ids:
        rec = await db.get(ContentDraft, draft_id)
        if rec is not None:
            fresh.append(rec)
    return GenerateContentResponse(drafts=fresh)


@router.post("/improve-content", response_model=DraftOut)
async def improve_content(
    payload: ImproveContentRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentDraft:
    try:
        draft = await content_service.improve_content(
            db,
            draft_id=payload.draft_id,
            instruction=payload.instruction,
            selected_text=payload.selected_text,
            user_id=current.id,
        )
    except AICapExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.improve_content",
        resource_type="content_draft",
        resource_id=str(draft.id),
        metadata={"instruction": payload.instruction[:200], "tokens": draft.tokens_used},
        request=request,
    )
    draft_id = draft.id
    await db.commit()
    fresh = await db.get(ContentDraft, draft_id)
    if fresh is None:
        raise HTTPException(status_code=500, detail="Draft vanished")
    return fresh


@router.post("/chat", response_model=AITextResponse)
async def ai_chat(
    payload: AIChatRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AITextResponse:
    try:
        result = await content_service.chat(
            db,
            brand_id=payload.brand_id,
            message=payload.message,
            language=payload.language,
            draft_id=payload.draft_id,
            history=[item.model_dump() for item in payload.history],
        )
    except AICapExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.chat",
        resource_type="brand",
        resource_id=str(payload.brand_id),
        metadata={"tokens": result["tokens_used"], "draft_id": str(payload.draft_id or "")},
        request=request,
    )
    await db.commit()
    return AITextResponse(**result)


@router.post("/generate-hashtags", response_model=HashtagResponse)
async def generate_hashtags(
    payload: GenerateHashtagsRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> HashtagResponse:
    try:
        result = await content_service.generate_hashtags(
            db,
            brand_id=payload.brand_id,
            platform=payload.platform,
            topic=payload.topic,
            language=payload.language,
            count=payload.count,
        )
    except AICapExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.generate_hashtags",
        resource_type="brand",
        resource_id=str(payload.brand_id),
        metadata={"tokens": result["tokens_used"], "count": len(result["hashtags"])},
        request=request,
    )
    await db.commit()
    return HashtagResponse(**result)


@router.post("/generate-reels-script", response_model=AITextResponse)
async def generate_reels_script(
    payload: GenerateReelsScriptRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AITextResponse:
    try:
        result = await content_service.generate_reels_script(
            db,
            brand_id=payload.brand_id,
            topic=payload.topic,
            language=payload.language,
            duration_seconds=payload.duration_seconds,
        )
    except AICapExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.generate_reels_script",
        resource_type="brand",
        resource_id=str(payload.brand_id),
        metadata={"tokens": result["tokens_used"], "duration_seconds": payload.duration_seconds},
        request=request,
    )
    await db.commit()
    return AITextResponse(**result)


@router.post("/generate-30-day-plan", response_model=AITextResponse)
async def generate_30_day_plan(
    payload: GeneratePlanRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AITextResponse:
    try:
        result = await content_service.generate_30_day_plan(
            db,
            brand_id=payload.brand_id,
            platform=payload.platform,
            topic=payload.topic,
            language=payload.language,
            days=payload.days,
        )
    except AICapExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.generate_30_day_plan",
        resource_type="brand",
        resource_id=str(payload.brand_id),
        metadata={"tokens": result["tokens_used"], "days": payload.days},
        request=request,
    )
    await db.commit()
    return AITextResponse(**result)


@router.get("/drafts", response_model=list[DraftOut])
async def list_drafts(
    brand_id: UUID | None = None,
    platform: str | None = None,
    starred: bool | None = None,
    limit: int = 50,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[ContentDraft]:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    return await content_service.list_drafts(
        db, brand_id=brand_id, platform=platform, starred=starred, limit=limit
    )


@router.get("/drafts/{draft_id}", response_model=DraftOut)
async def get_draft(
    draft_id: UUID,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentDraft:
    rec = await content_service.get_draft(db, draft_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return rec


@router.patch("/drafts/{draft_id}", response_model=DraftOut)
async def update_draft(
    draft_id: UUID,
    payload: DraftPatch,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentDraft:
    rec = await content_service.update_draft(db, draft_id, title=payload.title, body=payload.body)
    if rec is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.update_draft",
        resource_type="content_draft",
        resource_id=str(draft_id),
        request=request,
    )
    rec_id = rec.id
    await db.commit()
    fresh = await db.get(ContentDraft, rec_id)
    if fresh is None:
        raise HTTPException(status_code=500, detail="Draft vanished")
    return fresh


@router.post("/drafts/{draft_id}/star", response_model=DraftOut)
async def star_draft(
    draft_id: UUID,
    _: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentDraft:
    rec = await content_service.toggle_star(db, draft_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    rec_id = rec.id
    await db.commit()
    fresh = await db.get(ContentDraft, rec_id)
    if fresh is None:
        raise HTTPException(status_code=500, detail="Draft vanished")
    return fresh


@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await content_service.delete_draft(db, draft_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Draft not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="ai.delete_draft",
        resource_type="content_draft",
        resource_id=str(draft_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}


@router.get("/usage", response_model=AIUsageOut)
async def ai_usage(
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AIUsageOut:
    snap = await ai_service.get_usage_snapshot(db)
    return AIUsageOut(
        period=str(snap["period"]),
        tokens_used=int(snap["tokens_used"]),
        tokens_cap=int(snap["tokens_cap"]),
    )


@router.get("/stats", response_model=ContentStats)
async def content_stats(
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentStats:
    snap = await content_service.stats(db)
    return ContentStats(
        drafts_total=int(snap["drafts_total"]),
        drafts_starred=int(snap["drafts_starred"]),
        by_platform={k: int(v) for k, v in (snap["by_platform"] or {}).items()},
    )
