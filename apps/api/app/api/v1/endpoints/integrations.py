from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.smm import IntegrationConnectRequest, IntegrationProvider
from app.services import audit_service, integration_service
from app.services.integration_service import PROVIDERS, UnknownProviderError

router = APIRouter()


@router.get("", response_model=list[IntegrationProvider])
async def list_integrations(
    _: CurrentUser = Depends(require_permission("integrations.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[dict[str, object]]:
    return await integration_service.list_with_status(db)


@router.put("/{provider}", response_model=IntegrationProvider)
async def connect_provider(
    provider: str,
    payload: IntegrationConnectRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, object]:
    try:
        await integration_service.upsert(
            db,
            provider=provider,
            credentials=payload.credentials,
            user_id=current.id,
            label=payload.label,
            metadata=payload.metadata,
        )
    except UnknownProviderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="integrations.connect",
        resource_type="integration",
        resource_id=provider,
        metadata={"label": payload.label},
        request=request,
    )
    # Build the response BEFORE commit (post-commit some sessions invalidate state)
    items = await integration_service.list_with_status(db)
    await db.commit()

    matched = next((i for i in items if i["provider"] == provider), None)
    if matched is None:
        raise HTTPException(status_code=500, detail="Integration not found after upsert")
    return matched


@router.delete("/{provider}")
async def disconnect_provider(
    provider: str,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    deleted = await integration_service.disconnect(db, provider)
    if not deleted:
        raise HTTPException(status_code=404, detail="Integration not connected")
    await audit_service.record(
        db,
        user_id=current.id,
        action="integrations.disconnect",
        resource_type="integration",
        resource_id=provider,
        request=request,
    )
    await db.commit()
    return {"deleted": True}
