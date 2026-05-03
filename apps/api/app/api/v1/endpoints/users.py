from __future__ import annotations

import secrets
import string
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.core.db import get_db
from app.core.deps import CurrentUser, get_current_user, get_tenant_session, require_permission
from app.models.tenant_scoped import Role, UserMembership
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.tenant import InviteUserRequest, InvitedUserOut, UpdateUserRequest
from app.services import audit_service

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
        await public_db.execute(
            select(User).where(User.tenant_id == current.tenant.id, User.is_active.is_(True))
        )
    ).scalars()
    by_id = {u.id: u for u in rows}
    for uid in user_ids:
        if uid not in by_id:
            user = await public_db.get(User, uid)
            if user is not None:
                by_id[user.id] = user
    return list(by_id.values())


def _temporary_password(length: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits
    body = "".join(secrets.choice(alphabet) for _ in range(length - 2))
    return f"Nx{body}1"


async def _role_by_slug(db: AsyncSession, slug: str) -> Role:
    role = (await db.execute(select(Role).where(Role.slug == slug))).scalars().first()
    if role is None:
        raise HTTPException(status_code=400, detail="Role not found")
    return role


async def _primary_membership(db: AsyncSession, user_id: UUID) -> UserMembership | None:
    return (
        await db.execute(
            select(UserMembership)
            .where(UserMembership.user_id == user_id)
            .order_by(UserMembership.is_primary.desc(), UserMembership.created_at.asc())
            .limit(1)
        )
    ).scalars().first()


@router.post("", response_model=InvitedUserOut, status_code=201)
async def invite_user(
    payload: InviteUserRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("users.invite")),
    public_db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> InvitedUserOut:
    role = await _role_by_slug(tenant_db, payload.role_slug)
    existing = (
        await public_db.execute(
            select(User).where(or_(User.email == payload.email, User.phone == payload.phone))
        )
    ).scalars().first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="User with this email or phone exists")

    temporary_password = _temporary_password()
    user = User(
        tenant_id=current.tenant.id,
        email=str(payload.email),
        phone=payload.phone,
        password_hash=hash_password(temporary_password),
        full_name=payload.full_name,
        role=role.slug,
        is_active=True,
        is_verified=True,
    )
    public_db.add(user)
    await public_db.flush()

    membership = UserMembership(
        user_id=user.id,
        department_id=payload.department_id,
        role_id=role.id,
        is_primary=True,
        invited_by=current.id,
    )
    tenant_db.add(membership)
    await audit_service.record(
        tenant_db,
        user_id=current.id,
        action="users.invite",
        resource_type="user",
        resource_id=str(user.id),
        metadata={"email": user.email, "role": role.slug},
        request=request,
    )
    await tenant_db.commit()
    await public_db.commit()
    return InvitedUserOut(
        id=user.id,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        role=user.role,
        temporary_password=temporary_password,
    )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    current: CurrentUser = Depends(require_permission("users.read")),
    public_db: AsyncSession = Depends(get_db),
) -> User:
    user = await public_db.get(User, user_id)
    if user is None or user.tenant_id != current.tenant.id or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    payload: UpdateUserRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("users.update")),
    public_db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> User:
    user = await public_db.get(User, user_id)
    if user is None or user.tenant_id != current.tenant.id or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")

    fields = payload.model_dump(exclude_unset=True)
    membership = await _primary_membership(tenant_db, user_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    if "full_name" in fields:
        user.full_name = payload.full_name
    if payload.role_slug is not None:
        role = await _role_by_slug(tenant_db, payload.role_slug)
        membership.role_id = role.id
        user.role = role.slug
    if "department_id" in fields:
        membership.department_id = payload.department_id

    await audit_service.record(
        tenant_db,
        user_id=current.id,
        action="users.update",
        resource_type="user",
        resource_id=str(user.id),
        metadata=fields,
        request=request,
    )
    await tenant_db.commit()
    await public_db.commit()
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("users.remove")),
    public_db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="You cannot remove yourself")

    user = await public_db.get(User, user_id)
    if user is None or user.tenant_id != current.tenant.id or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "owner":
        raise HTTPException(status_code=400, detail="Owner cannot be removed")

    memberships = (
        await tenant_db.execute(select(UserMembership).where(UserMembership.user_id == user_id))
    ).scalars()
    for membership in memberships:
        await tenant_db.delete(membership)
    user.is_active = False

    await audit_service.record(
        tenant_db,
        user_id=current.id,
        action="users.remove",
        resource_type="user",
        resource_id=str(user.id),
        metadata={"email": user.email},
        request=request,
    )
    await tenant_db.commit()
    await public_db.commit()
    return {"deleted": True}
