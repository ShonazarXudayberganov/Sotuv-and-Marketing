from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.tenant_scoped import AuditLog
from app.schemas.tenant import AuditLogOut

router = APIRouter()


@router.get("", response_model=list[AuditLogOut])
async def list_entries(
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    _: CurrentUser = Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if since:
        stmt = stmt.where(AuditLog.created_at >= since)
    rows = (await db.execute(stmt)).scalars()
    return list(rows)
