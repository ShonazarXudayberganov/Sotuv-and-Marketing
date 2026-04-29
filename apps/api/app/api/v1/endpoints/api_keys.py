from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.tenant_scoped import ApiKey
from app.schemas.tasks import ApiKeyCreate, ApiKeyCreated, ApiKeyOut
from app.services import api_key_service, audit_service

router = APIRouter()


@router.get("", response_model=list[ApiKeyOut])
async def list_api_keys(
    _: CurrentUser = Depends(require_permission("api_keys.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[ApiKey]:
    rows = (await db.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))).scalars()
    return list(rows)


@router.post("", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(
    payload: ApiKeyCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("api_keys.create")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ApiKeyCreated:
    key, plain = await api_key_service.create(
        db,
        user_id=current.id,
        name=payload.name,
        scopes=payload.scopes,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        expires_in_days=payload.expires_in_days,
    )
    await audit_service.record(
        db,
        user_id=current.id,
        action="api_keys.create",
        resource_type="api_key",
        resource_id=str(key.id),
        metadata={"name": key.name, "scopes": list(key.scopes)},
        request=request,
    )
    await db.commit()
    return ApiKeyCreated(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        scopes=list(key.scopes),
        rate_limit_per_minute=key.rate_limit_per_minute,
        expires_at=key.expires_at,
        last_used_at=key.last_used_at,
        revoked_at=key.revoked_at,
        created_at=key.created_at,
        plaintext_key=plain,
    )


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("api_keys.revoke")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, str]:
    key = await db.get(ApiKey, key_id)
    if key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    key.revoked_at = datetime.now(UTC)
    await audit_service.record(
        db,
        user_id=current.id,
        action="api_keys.revoke",
        resource_type="api_key",
        resource_id=str(key_id),
        request=request,
    )
    await db.commit()
    return {"status": "revoked"}
