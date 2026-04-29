"""Audit log writer — used by endpoints to record sensitive actions."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant_scoped import AuditLog


async def record(
    session: AsyncSession,
    *,
    user_id: Any,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    metadata: dict[str, object] | None = None,
    request: Request | None = None,
) -> AuditLog:
    user_agent: str | None = None
    if request is not None:
        ua = request.headers.get("user-agent")
        if ua:
            user_agent = ua[:500]

    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_=metadata,
        ip_address=_client_ip(request) if request else None,
        user_agent=user_agent,
    )
    session.add(entry)
    await session.flush()
    return entry


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    if request.client:
        return request.client.host[:45]
    return None
