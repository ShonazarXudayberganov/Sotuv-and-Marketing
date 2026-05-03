from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.ads import (
    AdAccountOut,
    AdsInsightsOut,
    AdsOverview,
    AdsTimePoint,
    CampaignDraftRequest,
    CampaignOut,
    CampaignPatch,
    CampaignWithMetrics,
    MetricsOut,
    SyncResult,
)
from app.services import ads_service, audit_service

router = APIRouter()


@router.get("/accounts", response_model=list[AdAccountOut])
async def list_accounts(
    network: str | None = None,
    _: CurrentUser = Depends(require_permission("ads.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[AdAccountOut]:
    rows = await ads_service.list_accounts(db, network=network)
    return [AdAccountOut.model_validate(r) for r in rows]


@router.post("/accounts/sync-mock", response_model=SyncResult)
async def sync_accounts_mock(
    request: Request,
    current: CurrentUser = Depends(require_permission("ads.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> SyncResult:
    inserted = await ads_service.sync_accounts_mock(db)
    await audit_service.record(
        db,
        user_id=current.id,
        action="ads.sync_accounts_mock",
        resource_type="ads",
        metadata={"inserted": inserted},
        request=request,
    )
    await db.commit()
    return SyncResult(inserted=inserted)


@router.post("/campaigns/sync-mock", response_model=SyncResult)
async def sync_campaigns_mock(
    request: Request,
    current: CurrentUser = Depends(require_permission("ads.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> SyncResult:
    inserted = await ads_service.sync_campaigns_mock(db)
    await audit_service.record(
        db,
        user_id=current.id,
        action="ads.sync_campaigns_mock",
        resource_type="ads",
        metadata={"inserted": inserted},
        request=request,
    )
    await db.commit()
    return SyncResult(inserted=inserted)


@router.post("/snapshot", response_model=SyncResult)
async def snapshot_metrics(
    request: Request,
    current: CurrentUser = Depends(require_permission("ads.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> SyncResult:
    inserted = await ads_service.record_metrics_snapshot(db)
    await audit_service.record(
        db,
        user_id=current.id,
        action="ads.snapshot",
        resource_type="ads",
        metadata={"inserted": inserted},
        request=request,
    )
    await db.commit()
    return SyncResult(inserted=inserted)


@router.get("/campaigns", response_model=list[CampaignWithMetrics])
async def list_campaigns(
    account_id: UUID | None = None,
    network: str | None = None,
    status: str | None = None,
    limit: int = 200,
    _: CurrentUser = Depends(require_permission("ads.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[CampaignWithMetrics]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    rows = await ads_service.list_campaigns(
        db, account_id=account_id, network=network, status=status, limit=limit
    )
    out: list[CampaignWithMetrics] = []
    for c in rows:
        latest = await ads_service.latest_metrics(db, c.id)
        metrics = (
            MetricsOut(
                impressions=latest.impressions,
                clicks=latest.clicks,
                conversions=latest.conversions,
                spend=latest.spend,
                revenue=latest.revenue,
                ctr=latest.ctr,
                cpc=latest.cpc,
                cpa=latest.cpa,
                sampled_at=latest.sampled_at,
            )
            if latest is not None
            else None
        )
        out.append(
            CampaignWithMetrics(
                **CampaignOut.model_validate(c).model_dump(),
                metrics=metrics,
            )
        )
    return out


@router.get("/campaigns/{campaign_id}", response_model=CampaignWithMetrics)
async def get_campaign(
    campaign_id: UUID,
    _: CurrentUser = Depends(require_permission("ads.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> CampaignWithMetrics:
    rec = await ads_service.get_campaign(db, campaign_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    latest = await ads_service.latest_metrics(db, rec.id)
    metrics = (
        MetricsOut(
            impressions=latest.impressions,
            clicks=latest.clicks,
            conversions=latest.conversions,
            spend=latest.spend,
            revenue=latest.revenue,
            ctr=latest.ctr,
            cpc=latest.cpc,
            cpa=latest.cpa,
            sampled_at=latest.sampled_at,
        )
        if latest is not None
        else None
    )
    return CampaignWithMetrics(
        **CampaignOut.model_validate(rec).model_dump(), metrics=metrics
    )


@router.post("/campaigns", response_model=CampaignOut, status_code=201)
async def create_campaign_draft(
    payload: CampaignDraftRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("ads.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> CampaignOut:
    try:
        rec = await ads_service.create_draft(
            db,
            account_id=payload.account_id,
            name=payload.name,
            objective=payload.objective,
            daily_budget=payload.daily_budget,
            currency=payload.currency,
            audience=payload.audience,
            creative=payload.creative,
            notes=payload.notes,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await audit_service.record(
        db,
        user_id=current.id,
        action="ads.create_draft",
        resource_type="campaign",
        resource_id=str(rec.id),
        request=request,
    )
    response = CampaignOut.model_validate(rec)
    await db.commit()
    return response


@router.patch("/campaigns/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: UUID,
    payload: CampaignPatch,
    request: Request,
    current: CurrentUser = Depends(require_permission("ads.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> CampaignOut:
    rec = await ads_service.update_campaign(
        db, campaign_id, payload=payload.model_dump(exclude_unset=True)
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="ads.update_campaign",
        resource_type="campaign",
        resource_id=str(campaign_id),
        request=request,
    )
    response = CampaignOut.model_validate(rec)
    await db.commit()
    return response


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("ads.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await ads_service.delete_campaign(db, campaign_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="ads.delete_campaign",
        resource_type="campaign",
        resource_id=str(campaign_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}


@router.get("/overview", response_model=AdsOverview)
async def overview(
    network: str | None = None,
    _: CurrentUser = Depends(require_permission("ads.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AdsOverview:
    return AdsOverview.model_validate(await ads_service.overview(db, network=network))


@router.get("/timeseries", response_model=list[AdsTimePoint])
async def timeseries(
    days: int = 14,
    _: CurrentUser = Depends(require_permission("ads.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[AdsTimePoint]:
    try:
        rows = await ads_service.timeseries(db, days=days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [AdsTimePoint.model_validate(r) for r in rows]


@router.get("/insights", response_model=AdsInsightsOut)
async def insights(
    _: CurrentUser = Depends(require_permission("ads.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AdsInsightsOut:
    return AdsInsightsOut.model_validate(await ads_service.insights(db))
