from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.analytics import (
    AnalyticsOverview,
    AnalyticsTimePoint,
    InsightsOut,
    OptimalTimes,
    SnapshotResult,
    TopPost,
)
from app.services import analytics_service, audit_service

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def overview(
    brand_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AnalyticsOverview:
    snap = await analytics_service.overview(db, brand_id=brand_id)
    return AnalyticsOverview.model_validate(snap)


@router.get("/timeseries", response_model=list[AnalyticsTimePoint])
async def timeseries(
    brand_id: UUID | None = None,
    days: int = 30,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[AnalyticsTimePoint]:
    try:
        rows = await analytics_service.timeseries(db, brand_id=brand_id, days=days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [AnalyticsTimePoint.model_validate(r) for r in rows]


@router.get("/top-posts", response_model=list[TopPost])
async def top_posts(
    brand_id: UUID | None = None,
    limit: int = 5,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[TopPost]:
    if limit < 1 or limit > 25:
        raise HTTPException(status_code=400, detail="limit must be 1..25")
    rows = await analytics_service.top_posts(db, brand_id=brand_id, limit=limit)
    return [TopPost.model_validate(r) for r in rows]


@router.get("/optimal-times", response_model=OptimalTimes)
async def optimal_times(
    brand_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> OptimalTimes:
    snap = await analytics_service.optimal_times(db, brand_id=brand_id)
    return OptimalTimes.model_validate(snap)


@router.get("/insights", response_model=InsightsOut)
async def insights(
    brand_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> InsightsOut:
    data = await analytics_service.insights(db, brand_id=brand_id)
    return InsightsOut.model_validate(data)


@router.post("/snapshot", response_model=SnapshotResult)
async def trigger_snapshot(
    request: Request,
    brand_id: UUID | None = None,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> SnapshotResult:
    inserted = await analytics_service.record_snapshot(db, brand_id=brand_id)
    await audit_service.record(
        db,
        user_id=current.id,
        action="analytics.snapshot",
        resource_type="analytics",
        metadata={"inserted": inserted, "brand_id": str(brand_id) if brand_id else None},
        request=request,
    )
    await db.commit()
    return SnapshotResult(inserted=inserted)
