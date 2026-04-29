from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import CurrentUser, get_current_user, get_tenant_session, require_permission
from app.models.tenant_scoped import UserMembership
from app.models.user import User
from app.schemas.auth import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def me(current: CurrentUser = Depends(get_current_user)) -> User:
    return current.user


@router.get("", response_model=list[UserOut])
async def list_users(
    current: CurrentUser = Depends(require_permission("users.read")),
    public_db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> list[User]:
    membership_rows = (await tenant_db.execute(select(UserMembership.user_id))).scalars()
    user_ids = list(membership_rows)
    # Always include the owner row that belongs to this tenant via FK
    rows = (
        await public_db.execute(select(User).where(User.tenant_id == current.tenant.id))
    ).scalars()
    by_id = {u.id: u for u in rows}
    for uid in user_ids:
        if uid not in by_id:
            user = await public_db.get(User, uid)
            if user is not None:
                by_id[user.id] = user
    return list(by_id.values())
