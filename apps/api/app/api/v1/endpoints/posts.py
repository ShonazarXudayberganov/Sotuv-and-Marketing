from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.smm import Post
from app.schemas.post import (
    CalendarDay,
    CalendarOut,
    PostCreateRequest,
    PostDetailOut,
    PostOut,
    PostReschedule,
    PostStats,
    PublicationOut,
)
from app.services import audit_service, post_service

router = APIRouter()


async def _detail(db: AsyncSession, post: Post) -> PostDetailOut:
    pubs = await post_service.list_publications(db, post.id)
    return PostDetailOut(
        id=post.id,
        brand_id=post.brand_id,
        draft_id=post.draft_id,
        title=post.title,
        body=post.body,
        media_urls=post.media_urls,
        status=post.status,
        scheduled_at=post.scheduled_at,
        published_at=post.published_at,
        last_error=post.last_error,
        created_at=post.created_at,
        updated_at=post.updated_at,
        publications=[PublicationOut.model_validate(p) for p in pubs],
    )


@router.get("", response_model=list[PostOut])
async def list_posts(
    brand_id: UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[Post]:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    return await post_service.list_posts(db, brand_id=brand_id, status=status, limit=limit)


@router.get("/calendar", response_model=CalendarOut)
async def post_calendar(
    start: datetime = Query(..., description="Inclusive UTC start of the window"),
    end: datetime = Query(..., description="Exclusive UTC end of the window"),
    brand_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> CalendarOut:
    if end <= start:
        raise HTTPException(status_code=400, detail="end must be after start")
    if (end - start) > timedelta(days=92):
        raise HTTPException(status_code=400, detail="window cannot exceed 92 days")

    # Normalise to UTC if the caller provided a naive datetime.
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)

    rows = await post_service.list_in_range(db, start=start, end=end, brand_id=brand_id)

    by_day: dict[str, list[PostOut]] = {}
    for p in rows:
        anchor = p.scheduled_at or p.published_at
        if anchor is None:
            continue
        day_key = anchor.astimezone(UTC).date().isoformat()
        by_day.setdefault(day_key, []).append(PostOut.model_validate(p))

    days: list[CalendarDay] = [
        CalendarDay(date=date_key, posts=posts) for date_key, posts in sorted(by_day.items())
    ]
    return CalendarOut(
        start=start.astimezone(UTC).isoformat(),
        end=end.astimezone(UTC).isoformat(),
        days=days,
    )


@router.get("/stats", response_model=PostStats)
async def post_stats(
    brand_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> PostStats:
    snap = await post_service.stats(db, brand_id=brand_id)
    return PostStats(total=int(snap["total"]), by_status=dict(snap["by_status"]))


@router.get("/{post_id}", response_model=PostDetailOut)
async def get_post(
    post_id: UUID,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> PostDetailOut:
    post = await post_service.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return await _detail(db, post)


@router.post("", response_model=PostDetailOut, status_code=201)
async def create_post(
    payload: PostCreateRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> PostDetailOut:
    try:
        post = await post_service.create_post(
            db,
            brand_id=payload.brand_id,
            body=payload.body,
            title=payload.title,
            media_urls=payload.media_urls,
            social_account_ids=payload.social_account_ids,
            scheduled_at=payload.scheduled_at,
            draft_id=payload.draft_id,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="posts.create",
        resource_type="post",
        resource_id=str(post.id),
        metadata={
            "brand_id": str(payload.brand_id),
            "platforms": len(payload.social_account_ids),
            "scheduled_at": payload.scheduled_at.isoformat() if payload.scheduled_at else None,
        },
        request=request,
    )
    response = await _detail(db, post)
    await db.commit()
    return response


@router.patch("/{post_id}", response_model=PostDetailOut)
async def reschedule_post(
    post_id: UUID,
    payload: PostReschedule,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> PostDetailOut:
    try:
        post = await post_service.reschedule(db, post_id, payload.scheduled_at)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    await audit_service.record(
        db,
        user_id=current.id,
        action="posts.reschedule",
        resource_type="post",
        resource_id=str(post_id),
        metadata={
            "scheduled_at": payload.scheduled_at.isoformat() if payload.scheduled_at else None,
        },
        request=request,
    )
    response = await _detail(db, post)
    await db.commit()
    return response


@router.post("/{post_id}/cancel", response_model=PostDetailOut)
async def cancel_post(
    post_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> PostDetailOut:
    try:
        post = await post_service.cancel(db, post_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="posts.cancel",
        resource_type="post",
        resource_id=str(post_id),
        request=request,
    )
    response = await _detail(db, post)
    await db.commit()
    return response


@router.post("/{post_id}/retry", response_model=PostDetailOut)
async def retry_post(
    post_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> PostDetailOut:
    try:
        post = await post_service.retry_post(db, post_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="posts.retry",
        resource_type="post",
        resource_id=str(post_id),
        request=request,
    )
    response = await _detail(db, post)
    await db.commit()
    return response


@router.post("/{post_id}/publish-now", response_model=PostDetailOut)
async def publish_now(
    post_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> PostDetailOut:
    post = await post_service.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.status not in {"draft", "scheduled", "failed", "partial"}:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish a post in status '{post.status}'",
        )
    post = await post_service.publish_now(db, post)
    await audit_service.record(
        db,
        user_id=current.id,
        action="posts.publish_now",
        resource_type="post",
        resource_id=str(post_id),
        metadata={"final_status": post.status},
        request=request,
    )
    response = await _detail(db, post)
    await db.commit()
    return response
