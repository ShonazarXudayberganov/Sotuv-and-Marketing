"""Grace period enforcement.

Once a tenant's subscription is in `read_only` state, write requests are
rejected (HTTP 402). `locked` rejects everything except billing endpoints. We
implement this as a FastAPI dependency rather than ASGI middleware because we
need access to the tenant DB session.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_tenant_session
from app.services import billing_service
from app.services.billing_service import GraceState

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Endpoints exempt from grace gating (auth, billing itself, health)
EXEMPT_PREFIXES = (
    "/api/v1/auth/",
    "/api/v1/billing/",
    "/api/v1/health",
    "/api/v1/notifications/ws",
    "/api/v1/2fa/",
)


async def enforce_grace(request: Request, db: AsyncSession = Depends(get_tenant_session)) -> None:
    path = request.url.path
    if any(path.startswith(p) for p in EXEMPT_PREFIXES):
        return

    sub = await billing_service.current_subscription(db)
    if sub is None:
        # Newly registered tenants can finish onboarding before choosing a plan.
        # Billing/status still reports "locked" so the UI can steer them to billing.
        return

    state = billing_service.evaluate_grace(sub)

    if state == GraceState.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Akkaunt qulflangan. Tarif faollashtirish uchun bilingni tekshiring.",
        )
    if state == GraceState.READ_ONLY and request.method.upper() in WRITE_METHODS:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Faqat o'qish rejimi: tarif muddati tugagan, to'lov qiling.",
        )
