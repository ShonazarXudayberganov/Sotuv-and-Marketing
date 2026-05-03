from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.core.permissions import PERMISSIONS
from app.models.tenant_scoped import Role, UserMembership
from app.schemas.tenant import RoleCreate, RoleOut, RoleUpdate
from app.services import audit_service

router = APIRouter()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return slug[:50] or "custom_role"


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


@router.post("", response_model=RoleOut, status_code=201)
async def create_role(
    payload: RoleCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("roles.create")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Role:
    slug = _slugify(payload.slug or payload.name)
    existing = (await db.execute(select(Role).where(Role.slug == slug))).scalars().first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Role slug already exists")

    role = Role(
        name=payload.name,
        slug=slug,
        description=payload.description,
        is_system=False,
        permissions=payload.permissions,
    )
    db.add(role)
    await db.flush()
    await audit_service.record(
        db,
        user_id=current.id,
        action="roles.create",
        resource_type="role",
        resource_id=str(role.id),
        metadata={"slug": role.slug},
        request=request,
    )
    await db.commit()
    return role


@router.patch("/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    request: Request,
    current: CurrentUser = Depends(require_permission("roles.update")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Role:
    role = await db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="System roles cannot be edited")

    fields = payload.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(role, key, value)
    await audit_service.record(
        db,
        user_id=current.id,
        action="roles.update",
        resource_type="role",
        resource_id=str(role.id),
        metadata=fields,
        request=request,
    )
    await db.commit()
    return role


@router.delete("/{role_id}")
async def delete_role(
    role_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("roles.delete")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    role = await db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="System roles cannot be deleted")

    in_use = (
        await db.execute(select(UserMembership).where(UserMembership.role_id == role_id).limit(1))
    ).first()
    if in_use is not None:
        raise HTTPException(status_code=409, detail="Role is assigned to at least one user")

    await db.delete(role)
    await audit_service.record(
        db,
        user_id=current.id,
        action="roles.delete",
        resource_type="role",
        resource_id=str(role_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}
