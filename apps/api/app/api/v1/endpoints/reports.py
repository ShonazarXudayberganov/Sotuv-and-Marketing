from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.reports import (
    CohortRow,
    FunnelOut,
    ReportsInsightsOut,
    ReportsOverview,
    SavedReportCreate,
    SavedReportOut,
    SavedReportPatch,
)
from app.services import audit_service, reports_service

router = APIRouter()


@router.get("/overview", response_model=ReportsOverview)
async def overview(
    days: int = 30,
    _: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ReportsOverview:
    try:
        snap = await reports_service.overview(db, days=days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReportsOverview.model_validate(snap)


@router.get("/funnel", response_model=FunnelOut)
async def funnel(
    _: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> FunnelOut:
    return FunnelOut.model_validate(await reports_service.funnel(db))


@router.get("/cohorts", response_model=list[CohortRow])
async def cohorts(
    months: int = 6,
    _: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[CohortRow]:
    try:
        rows = await reports_service.contact_cohorts(db, months=months)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [CohortRow.model_validate(r) for r in rows]


@router.get("/insights", response_model=ReportsInsightsOut)
async def insights(
    days: int = 30,
    _: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ReportsInsightsOut:
    try:
        data = await reports_service.insights(db, days=days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReportsInsightsOut.model_validate(data)


# ─────────── Saved reports CRUD ───────────


@router.get("/saved", response_model=list[SavedReportOut])
async def list_saved(
    _: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[SavedReportOut]:
    rows = await reports_service.list_saved(db)
    return [SavedReportOut.model_validate(r) for r in rows]


@router.post("/saved", response_model=SavedReportOut, status_code=201)
async def create_saved(
    payload: SavedReportCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> SavedReportOut:
    try:
        rec = await reports_service.create_saved(
            db,
            name=payload.name,
            description=payload.description,
            definition=payload.definition,
            is_pinned=payload.is_pinned,
            department_id=payload.department_id,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await audit_service.record(
        db,
        user_id=current.id,
        action="reports.create_saved",
        resource_type="report",
        resource_id=str(rec.id),
        request=request,
    )
    response = SavedReportOut.model_validate(rec)
    await db.commit()
    return response


@router.patch("/saved/{report_id}", response_model=SavedReportOut)
async def update_saved(
    report_id: UUID,
    payload: SavedReportPatch,
    request: Request,
    current: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> SavedReportOut:
    rec = await reports_service.update_saved(
        db, report_id, payload=payload.model_dump(exclude_unset=True)
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="Report not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="reports.update_saved",
        resource_type="report",
        resource_id=str(report_id),
        request=request,
    )
    response = SavedReportOut.model_validate(rec)
    await db.commit()
    return response


@router.delete("/saved/{report_id}")
async def delete_saved(
    report_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await reports_service.delete_saved(db, report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="reports.delete_saved",
        resource_type="report",
        resource_id=str(report_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}


# ─────────── Export ───────────


@router.get("/export/{kind}.csv")
async def export_csv(
    kind: str,
    _: CurrentUser = Depends(require_permission("reports.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Response:
    try:
        body = await reports_service.export_csv(db, kind=kind)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{kind}.csv"'},
    )
