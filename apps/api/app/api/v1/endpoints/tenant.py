from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import CurrentUser, get_current_user, require_permission
from app.models.tenant import Tenant
from app.schemas.tenant import TenantOut, TenantUpdate
from app.services import audit_service

router = APIRouter()


@router.get("/me", response_model=TenantOut)
async def get_my_tenant(current: CurrentUser = Depends(get_current_user)) -> Tenant:
    return current.tenant


@router.patch("/me", response_model=TenantOut)
async def update_my_tenant(
    payload: TenantUpdate,
    request: Request,
    current: CurrentUser = Depends(require_permission("tenant.update")),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    tenant = await db.get(Tenant, current.tenant.id)
    assert tenant is not None
    if payload.name is not None:
        tenant.name = payload.name
    if payload.industry is not None:
        tenant.industry = payload.industry
    await db.flush()
    await audit_service.record(
        db,
        user_id=current.id,
        action="tenant.update",
        resource_type="tenant",
        resource_id=str(tenant.id),
        metadata=payload.model_dump(exclude_none=True),
        request=request,
    )
    await db.commit()
    await db.refresh(tenant)
    return tenant
