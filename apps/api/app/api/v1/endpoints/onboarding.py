"""Onboarding wizard endpoints — stateless save-as-you-go.

The frontend wizard PATCHes individual steps (company info, departments, etc.)
which already have dedicated endpoints. This router exposes lightweight helpers
to track progress and finalize.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.tenant import OnboardingState
from app.services import audit_service

router = APIRouter()


@router.post("/complete")
async def complete_onboarding(
    payload: OnboardingState,
    request: Request,
    current: CurrentUser = Depends(require_permission("tenant.update")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, str]:
    await audit_service.record(
        db,
        user_id=current.id,
        action="onboarding.complete",
        resource_type="tenant",
        resource_id=str(current.tenant.id),
        metadata={
            "departments": payload.departments,
            "modules": payload.selected_modules,
            "plan": payload.selected_plan,
        },
        request=request,
    )
    await db.commit()
    return {"status": "ok"}
