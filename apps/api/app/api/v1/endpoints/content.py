from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.smm import ContentDraft
from app.schemas.content import (
    AIUsageOut,
    ContentStats,
    DraftOut,
    DraftPatch,
    GeneratePostRequest,
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
