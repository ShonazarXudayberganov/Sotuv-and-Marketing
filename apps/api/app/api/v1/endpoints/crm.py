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
)
from app.services import audit_service, contact_service

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
