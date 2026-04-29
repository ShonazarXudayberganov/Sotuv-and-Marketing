from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    CurrentUser,
    get_tenant_session,
    require_permission,
)
from app.models.tenant_scoped import Department
from app.schemas.tenant import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.services import audit_service

router = APIRouter()


@router.get("", response_model=list[DepartmentOut])
async def list_departments(
    _: CurrentUser = Depends(require_permission("departments.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[Department]:
    rows = (await db.execute(select(Department).order_by(Department.sort_order))).scalars()
    return list(rows)


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: DepartmentCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("departments.create")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Department:
    dept = Department(**payload.model_dump())
    db.add(dept)
    await db.flush()
    await audit_service.record(
        db,
        user_id=current.id,
        action="departments.create",
        resource_type="department",
        resource_id=str(dept.id),
        metadata=payload.model_dump(),
        request=request,
    )
    await db.commit()
    return dept


@router.patch("/{dept_id}", response_model=DepartmentOut)
async def update_department(
    dept_id: UUID,
    payload: DepartmentUpdate,
    request: Request,
    current: CurrentUser = Depends(require_permission("departments.update")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Department:
    dept = await db.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="Department not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(dept, field, value)
    await db.flush()
    await audit_service.record(
        db,
        user_id=current.id,
        action="departments.update",
        resource_type="department",
        resource_id=str(dept.id),
        metadata=payload.model_dump(exclude_none=True),
        request=request,
    )
    await db.commit()
    return dept


@router.delete("/{dept_id}")
async def delete_department(
    dept_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("departments.delete")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, str]:
    dept = await db.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="Department not found")
    await db.delete(dept)
    await audit_service.record(
        db,
        user_id=current.id,
        action="departments.delete",
        resource_type="department",
        resource_id=str(dept_id),
        request=request,
    )
    await db.commit()
    return {"status": "deleted"}
