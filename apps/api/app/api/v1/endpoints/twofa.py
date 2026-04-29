from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user, get_tenant_session
from app.schemas.tasks import TwoFactorSetupOut, TwoFactorVerifyRequest
from app.services import audit_service, twofa_service

router = APIRouter()


@router.post("/setup", response_model=TwoFactorSetupOut)
async def setup_2fa(
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> TwoFactorSetupOut:
    record, qr, backup_codes = await twofa_service.begin_setup(
        db, current.id, account_label=current.user.email
    )
    await audit_service.record(
        db,
        user_id=current.id,
        action="2fa.setup_started",
        resource_type="user",
        resource_id=str(current.id),
        request=request,
    )
    await db.commit()
    return TwoFactorSetupOut(secret=record.secret, qr_data_url=qr, backup_codes=backup_codes)


@router.post("/verify")
async def verify_2fa(
    payload: TwoFactorVerifyRequest,
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    ok = await twofa_service.verify_and_enable(db, current.id, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid code")
    await audit_service.record(
        db,
        user_id=current.id,
        action="2fa.enabled",
        resource_type="user",
        resource_id=str(current.id),
        request=request,
    )
    await db.commit()
    return {"enabled": True}


@router.post("/disable")
async def disable_2fa(
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    await twofa_service.disable(db, current.id)
    await audit_service.record(
        db,
        user_id=current.id,
        action="2fa.disabled",
        resource_type="user",
        resource_id=str(current.id),
        request=request,
    )
    await db.commit()
    return {"enabled": False}
