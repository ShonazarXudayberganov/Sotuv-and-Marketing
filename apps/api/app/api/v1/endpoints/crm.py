from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.crm import (
    ActivityCreate,
    ActivityOut,
    AiScoreOut,
    ContactCreate,
    ContactOut,
    ContactPatch,
    ContactStats,
    DealCreate,
    DealOut,
    DealPatch,
    DealStats,
    ForecastOut,
    PipelineOut,
    PipelineWithStages,
    StageOut,
)
from app.services import audit_service, contact_service, deal_service

router = APIRouter()


@router.get("/contacts", response_model=list[ContactOut])
async def list_contacts(
    query: str | None = None,
    status: str | None = None,
    department_id: UUID | None = None,
    min_score: int | None = None,
    limit: int = 50,
    offset: int = 0,
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[ContactOut]:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    rows = await contact_service.list_contacts(
        db,
        query=query,
        status=status,
        department_id=department_id,
        min_score=min_score,
        limit=limit,
        offset=max(0, offset),
    )
    return [ContactOut.model_validate(r) for r in rows]


@router.get("/contacts/stats", response_model=ContactStats)
async def contact_stats(
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContactStats:
    snap = await contact_service.stats(db)
    return ContactStats.model_validate(snap)


@router.get("/contacts/{contact_id}", response_model=ContactOut)
async def get_contact(
    contact_id: UUID,
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContactOut:
    rec = await contact_service.get_contact(db, contact_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactOut.model_validate(rec)


@router.post("/contacts", response_model=ContactOut, status_code=201)
async def create_contact(
    payload: ContactCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContactOut:
    try:
        rec = await contact_service.create_contact(
            db, payload=payload.model_dump(exclude_unset=True), user_id=current.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await audit_service.record(
        db,
        user_id=current.id,
        action="contacts.create",
        resource_type="contact",
        resource_id=str(rec.id),
        request=request,
    )
    response = ContactOut.model_validate(rec)
    await db.commit()
    return response


@router.patch("/contacts/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: UUID,
    payload: ContactPatch,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ContactOut:
    rec = await contact_service.update_contact(
        db, contact_id, payload=payload.model_dump(exclude_unset=True)
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="contacts.update",
        resource_type="contact",
        resource_id=str(contact_id),
        request=request,
    )
    response = ContactOut.model_validate(rec)
    await db.commit()
    return response


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await contact_service.delete_contact(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="contacts.delete",
        resource_type="contact",
        resource_id=str(contact_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}


@router.get("/contacts/{contact_id}/activities", response_model=list[ActivityOut])
async def list_activities(
    contact_id: UUID,
    limit: int = 50,
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[ActivityOut]:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    rows = await contact_service.list_activities(db, contact_id, limit=limit)
    return [ActivityOut.model_validate(r) for r in rows]


@router.post(
    "/contacts/{contact_id}/activities",
    response_model=ActivityOut,
    status_code=201,
)
async def add_activity(
    contact_id: UUID,
    payload: ActivityCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ActivityOut:
    try:
        rec = await contact_service.add_activity(
            db,
            contact_id=contact_id,
            kind=payload.kind,
            title=payload.title,
            body=payload.body,
            direction=payload.direction,
            channel=payload.channel,
            duration_seconds=payload.duration_seconds,
            metadata=payload.metadata,
            occurred_at=payload.occurred_at,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await audit_service.record(
        db,
        user_id=current.id,
        action="contacts.activity",
        resource_type="contact",
        resource_id=str(contact_id),
        metadata={"kind": payload.kind, "channel": payload.channel},
        request=request,
    )
    response = ActivityOut.model_validate(rec)
    await db.commit()
    return response


@router.post("/contacts/{contact_id}/rescore", response_model=AiScoreOut)
async def rescore_contact(
    contact_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AiScoreOut:
    result = await contact_service.score_with_ai(db, contact_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    score, reason = result
    await audit_service.record(
        db,
        user_id=current.id,
        action="contacts.rescore",
        resource_type="contact",
        resource_id=str(contact_id),
        metadata={"score": score},
        request=request,
    )
    await db.commit()
    return AiScoreOut(score=score, reason=reason)


# ─────────── Pipelines ───────────


@router.get("/pipelines", response_model=list[PipelineWithStages])
async def list_pipelines(
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[PipelineWithStages]:
    pipelines = await deal_service.list_pipelines(db)
    out: list[PipelineWithStages] = []
    for p in pipelines:
        stages = await deal_service.list_stages(db, p.id)
        out.append(
            PipelineWithStages(
                **PipelineOut.model_validate(p).model_dump(),
                stages=[StageOut.model_validate(s) for s in stages],
            )
        )
    return out


@router.get("/pipelines/{pipeline_id}/stages", response_model=list[StageOut])
async def list_stages(
    pipeline_id: UUID,
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[StageOut]:
    pipeline = await deal_service.get_pipeline(db, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    stages = await deal_service.list_stages(db, pipeline_id)
    return [StageOut.model_validate(s) for s in stages]


# ─────────── Deals ───────────


@router.get("/deals", response_model=list[DealOut])
async def list_deals(
    pipeline_id: UUID | None = None,
    stage_id: UUID | None = None,
    contact_id: UUID | None = None,
    assignee_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[DealOut]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    rows = await deal_service.list_deals(
        db,
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        contact_id=contact_id,
        assignee_id=assignee_id,
        status=status,
        limit=limit,
    )
    return [DealOut.model_validate(r) for r in rows]


@router.get("/deals/forecast", response_model=ForecastOut)
async def deal_forecast(
    pipeline_id: UUID | None = None,
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ForecastOut:
    snap = await deal_service.forecast(db, pipeline_id=pipeline_id)
    return ForecastOut.model_validate(snap)


@router.get("/deals/stats", response_model=DealStats)
async def deal_stats(
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> DealStats:
    snap = await deal_service.stats(db)
    return DealStats.model_validate(snap)


@router.get("/contacts/{contact_id}/deals", response_model=list[DealOut])
async def contact_deals(
    contact_id: UUID,
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[DealOut]:
    rows = await deal_service.list_deals(db, contact_id=contact_id, limit=200)
    return [DealOut.model_validate(r) for r in rows]


@router.get("/deals/{deal_id}", response_model=DealOut)
async def get_deal(
    deal_id: UUID,
    _: CurrentUser = Depends(require_permission("crm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> DealOut:
    rec = await deal_service.get_deal(db, deal_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return DealOut.model_validate(rec)


@router.post("/deals", response_model=DealOut, status_code=201)
async def create_deal(
    payload: DealCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> DealOut:
    try:
        rec = await deal_service.create_deal(
            db,
            title=payload.title,
            contact_id=payload.contact_id,
            pipeline_id=payload.pipeline_id,
            stage_id=payload.stage_id,
            amount=payload.amount,
            currency=payload.currency,
            expected_close_at=payload.expected_close_at,
            assignee_id=payload.assignee_id,
            department_id=payload.department_id,
            notes=payload.notes,
            tags=payload.tags,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await audit_service.record(
        db,
        user_id=current.id,
        action="deals.create",
        resource_type="deal",
        resource_id=str(rec.id),
        request=request,
    )
    response = DealOut.model_validate(rec)
    await db.commit()
    return response


@router.patch("/deals/{deal_id}", response_model=DealOut)
async def update_deal(
    deal_id: UUID,
    payload: DealPatch,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> DealOut:
    try:
        rec = await deal_service.update_deal(
            db,
            deal_id,
            payload=payload.model_dump(exclude_unset=True),
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if rec is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="deals.update",
        resource_type="deal",
        resource_id=str(deal_id),
        request=request,
    )
    response = DealOut.model_validate(rec)
    await db.commit()
    return response


@router.post("/deals/{deal_id}/win", response_model=DealOut)
async def win_deal(
    deal_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> DealOut:
    try:
        rec = await deal_service.win_deal(db, deal_id, user_id=current.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if rec is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="deals.win",
        resource_type="deal",
        resource_id=str(deal_id),
        request=request,
    )
    response = DealOut.model_validate(rec)
    await db.commit()
    return response


@router.post("/deals/{deal_id}/lose", response_model=DealOut)
async def lose_deal(
    deal_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> DealOut:
    try:
        rec = await deal_service.lose_deal(db, deal_id, user_id=current.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if rec is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="deals.lose",
        resource_type="deal",
        resource_id=str(deal_id),
        request=request,
    )
    response = DealOut.model_validate(rec)
    await db.commit()
    return response


@router.delete("/deals/{deal_id}")
async def delete_deal(
    deal_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("crm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await deal_service.delete_deal(db, deal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Deal not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="deals.delete",
        resource_type="deal",
        resource_id=str(deal_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}
