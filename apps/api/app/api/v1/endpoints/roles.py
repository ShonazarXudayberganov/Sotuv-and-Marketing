from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.core.permissions import PERMISSIONS
from app.models.tenant_scoped import Role
from app.schemas.tenant import RoleOut

router = APIRouter()


@router.get("", response_model=list[RoleOut])
async def list_roles(
    _: CurrentUser = Depends(require_permission("roles.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[Role]:
    rows = (await db.execute(select(Role).order_by(Role.is_system.desc(), Role.name))).scalars()
    return list(rows)


@router.get("/permissions", response_model=list[str])
async def list_known_permissions(
    _: CurrentUser = Depends(require_permission("roles.read")),
) -> list[str]:
    return list(PERMISSIONS)


@router.get("/me", response_model=list[str])
async def my_permissions(
    current: CurrentUser = Depends(require_permission("tenant.read")),
) -> list[str]:
    return sorted(current.permissions)
