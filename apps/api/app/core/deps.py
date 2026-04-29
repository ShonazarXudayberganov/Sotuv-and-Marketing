"""FastAPI dependencies: current user, tenant DB session, permission gate."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, get_session_factory
from app.core.tenancy import validate_schema_name
from app.models.tenant import Tenant
from app.models.tenant_scoped import Role, UserMembership
from app.models.user import User


class CurrentUser:
    def __init__(
        self,
        user: User,
        tenant: Tenant,
        permissions: set[str],
        membership_id: UUID | None,
        role_slug: str,
    ) -> None:
        self.user = user
        self.tenant = tenant
        self.permissions = permissions
        self.membership_id = membership_id
        self.role_slug = role_slug

    @property
    def id(self) -> UUID:
        return self.user.id

    def has(self, permission: str) -> bool:
        return permission in self.permissions


def _require_state(request: Request, key: str) -> str:
    state = request.scope.get("state") or {}
    value = state.get(key)
    if not value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return str(value)


async def get_tenant_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a session whose search_path is set to the caller's tenant schema."""
    schema = validate_schema_name(_require_state(request, "tenant_schema"))
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(text(f"SET search_path TO {schema}, public"))
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    request: Request,
    public_db: AsyncSession = Depends(get_db),
    tenant_db: AsyncSession = Depends(get_tenant_session),
) -> CurrentUser:
    user_id = UUID(_require_state(request, "user_id"))
    tenant_id = UUID(_require_state(request, "tenant_id"))

    user = await public_db.get(User, user_id)
    tenant = await public_db.get(Tenant, tenant_id)
    if user is None or tenant is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Resolve role + permissions in tenant schema. Owner gets unrestricted.
    role_slug = (request.scope.get("state") or {}).get("role", "owner")

    membership_q = await tenant_db.execute(
        select(UserMembership).where(UserMembership.user_id == user_id)
    )
    membership = membership_q.scalars().first()

    permissions: set[str] = set()
    membership_id: UUID | None = None
    if membership is not None:
        membership_id = membership.id
        role_q = await tenant_db.execute(select(Role).where(Role.id == membership.role_id))
        role = role_q.scalars().first()
        if role:
            permissions = set(role.permissions or [])
            role_slug = role.slug
    if role_slug == "owner":
        # Owner role is implicit — they may exist without membership row in dev/test.
        from app.core.permissions import PERMISSIONS

        permissions.update(PERMISSIONS)

    return CurrentUser(
        user=user,
        tenant=tenant,
        permissions=permissions,
        membership_id=membership_id,
        role_slug=role_slug,
    )


def require_permission(*needed: str) -> Callable[..., Any]:
    """FastAPI dependency factory: 403 if user lacks any of the listed permissions."""

    async def _checker(
        current: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        missing = [p for p in needed if not current.has(p)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return current

    return _checker
