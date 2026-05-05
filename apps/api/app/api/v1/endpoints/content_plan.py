from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.smm import ContentPlanItem
from app.schemas.content_plan import (
    ContentPlanCreatePostRequest,
    ContentPlanImportResult,
    ContentPlanImportTextRequest,
    ContentPlanItemCreate,
    ContentPlanItemOut,
    ContentPlanItemUpdate,
)
from app.schemas.post import PostDetailOut, PublicationOut
from app.services import audit_service, content_plan_service, post_service

router = APIRouter()


def _out(item: ContentPlanItem) -> ContentPlanItemOut:
    return ContentPlanItemOut(
        id=item.id,
        brand_id=item.brand_id,
        post_id=item.post_id,
        platform=item.platform,
        title=item.title,
        idea=item.idea,
        goal=item.goal,
        cta=item.cta,
        status=item.status,
        planned_at=item.planned_at,
        source=item.source,
        sort_order=item.sort_order,
        metadata=item.metadata_,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _post_detail(db: AsyncSession, post_id: UUID) -> PostDetailOut:
    post = await post_service.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    pubs = await post_service.list_publications(db, post.id)
    return PostDetailOut(
        id=post.id,
        brand_id=post.brand_id,
        draft_id=post.draft_id,
        title=post.title,
        body=post.body,
        media_urls=post.media_urls,
        content_format=post.content_format,
        status=post.status,
        scheduled_at=post.scheduled_at,
        published_at=post.published_at,
        last_error=post.last_error,
        created_at=post.created_at,
        updated_at=post.updated_at,
        publications=[PublicationOut.model_validate(pub) for pub in pubs],
    )


@router.get("", response_model=list[ContentPlanItemOut])
async def list_items(
    brand_id: UUID | None = None,
    platform: str | None = None,
    status: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 200,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[ContentPlanItemOut]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    try:
        rows = await content_plan_service.list_items(
            db,
            brand_id=brand_id,
            platform=platform,
            status=status,
            start=start,
            end=end,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_out(item) for item in rows]


@router.post("", response_model=ContentPlanItemOut, status_code=201)
async def create_item(
    payload: ContentPlanItemCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentPlanItemOut:
    try:
        item = await content_plan_service.create_item(
            db,
            brand_id=payload.brand_id,
            platform=payload.platform,
            title=payload.title,
            idea=payload.idea,
            goal=payload.goal,
            cta=payload.cta,
            status=payload.status,
            planned_at=payload.planned_at,
            source=payload.source,
            sort_order=payload.sort_order,
            metadata=payload.metadata,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="content_plan.create",
        resource_type="content_plan",
        resource_id=str(item.id),
        metadata={"brand_id": str(item.brand_id), "status": item.status},
        request=request,
    )
    await db.commit()
    return _out(item)


@router.post("/import-text", response_model=ContentPlanImportResult, status_code=201)
async def import_text(
    payload: ContentPlanImportTextRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentPlanImportResult:
    try:
        items = await content_plan_service.import_text(
            db,
            brand_id=payload.brand_id,
            platform=payload.platform,
            topic=payload.topic,
            text_value=payload.text,
            start_date=payload.start_date,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="content_plan.import_text",
        resource_type="content_plan",
        metadata={
            "brand_id": str(payload.brand_id),
            "platform": payload.platform,
            "items": len(items),
        },
        request=request,
    )
    await db.commit()
    return ContentPlanImportResult(items=[_out(item) for item in items])


@router.patch("/{item_id}", response_model=ContentPlanItemOut)
async def update_item(
    item_id: UUID,
    payload: ContentPlanItemUpdate,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContentPlanItemOut:
    fields = payload.model_fields_set
    try:
        item = await content_plan_service.update_item(
            db,
            item_id,
            platform=payload.platform,
            title=payload.title,
            idea=payload.idea,
            goal=payload.goal,
            cta=payload.cta,
            status=payload.status,
            planned_at=payload.planned_at,
            planned_at_set="planned_at" in fields,
            sort_order=payload.sort_order,
            metadata=payload.metadata,
            metadata_set="metadata" in fields,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Plan item not found")

    await audit_service.record(
        db,
        user_id=current.id,
        action="content_plan.update",
        resource_type="content_plan",
        resource_id=str(item.id),
        request=request,
    )
    await db.commit()
    return _out(item)


@router.post("/{item_id}/create-post", response_model=PostDetailOut, status_code=201)
async def create_post_from_item(
    item_id: UUID,
    payload: ContentPlanCreatePostRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> PostDetailOut:
    try:
        result = await content_plan_service.create_post_from_item(
            db,
            item_id,
            social_account_ids=payload.social_account_ids,
            scheduled_at=payload.scheduled_at,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Plan item not found")
    item, post = result

    await audit_service.record(
        db,
        user_id=current.id,
        action="content_plan.create_post",
        resource_type="content_plan",
        resource_id=str(item.id),
        metadata={"post_id": str(post.id), "status": item.status},
        request=request,
    )
    response = await _post_detail(db, post.id)
    await db.commit()
    return response


@router.delete("/{item_id}")
async def delete_item(
    item_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await content_plan_service.delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plan item not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="content_plan.delete",
        resource_type="content_plan",
        resource_id=str(item_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}
