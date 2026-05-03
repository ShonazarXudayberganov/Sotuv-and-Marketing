"""User session tracking — backs the Active Sessions UI and refresh-token revocation."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenancy import validate_schema_name
from app.models.tenant_scoped import UserSession


def new_jti() -> str:
    return secrets.token_urlsafe(32)


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    if request.client:
        return request.client.host[:45]
    return None


def _user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    ua = request.headers.get("user-agent")
    return ua[:500] if ua else None


async def create(
    db: AsyncSession,
    *,
    schema_name: str,
    user_id: UUID,
    jti: str,
    request: Request | None,
) -> UserSession:
    """Insert a session row in the tenant's schema."""
    schema = validate_schema_name(schema_name)
    await db.execute(text(f"SET search_path TO {schema}, public"))
    record = UserSession(
        user_id=user_id,
        jti=jti,
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
        last_active_at=datetime.now(UTC),
    )
    db.add(record)
    await db.flush()
    return record


async def is_active_jti(db: AsyncSession, *, schema_name: str, jti: str) -> bool:
    schema = validate_schema_name(schema_name)
    await db.execute(text(f"SET search_path TO {schema}, public"))
    row = (await db.execute(select(UserSession).where(UserSession.jti == jti))).scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        return False
    row.last_active_at = datetime.now(UTC)
    return True


async def revoke_jti(db: AsyncSession, jti: str) -> None:
    """Revoke by jti — caller must already be in the right tenant schema."""
    row = (await db.execute(select(UserSession).where(UserSession.jti == jti))).scalar_one_or_none()
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)


async def list_active_for_user(db: AsyncSession, *, user_id: UUID) -> list[UserSession]:
    rows = (
        await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .order_by(UserSession.last_active_at.desc())
        )
    ).scalars()
    return list(rows)
