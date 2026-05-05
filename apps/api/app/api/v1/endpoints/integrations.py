from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.smm import (
    IntegrationConnectRequest,
    IntegrationProvider,
    MetaOAuthFinishRequest,
    MetaOAuthStartRequest,
    MetaOAuthStartResponse,
)
from app.services import audit_service, integration_service, meta_service
from app.services.integration_service import PROVIDERS, UnknownProviderError
from app.services.meta_service import MetaError

router = APIRouter()

META_STATE_TTL_MINUTES = 15


def _validate_redirect_uri(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin not in settings.CORS_ORIGINS:
        raise HTTPException(status_code=400, detail="redirect_uri origin is not allowed")
    return value


async def _provider_response(db: AsyncSession, provider: str) -> dict[str, object]:
    items = await integration_service.list_with_status(db)
    matched = next((i for i in items if i["provider"] == provider), None)
    if matched is None:
        raise HTTPException(status_code=500, detail="Integration not found after update")
    return matched


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
    matched = await _provider_response(db, provider)
    await db.commit()
    return matched


@router.post("/meta_app/oauth/start", response_model=MetaOAuthStartResponse)
async def start_meta_oauth(
    payload: MetaOAuthStartRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> MetaOAuthStartResponse:
    redirect_uri = _validate_redirect_uri(payload.redirect_uri)
    credentials = await integration_service.get_credentials(db, "meta_app")
    if not credentials or not credentials.get("app_id") or not credentials.get("app_secret"):
        raise HTTPException(
            status_code=400,
            detail="Avval Meta app_id va app_secret ni integratsiyalarda kiriting",
        )

    record = await integration_service.get_record(db, "meta_app")
    if record is None:
        raise HTTPException(status_code=400, detail="Meta app integratsiyasi topilmadi")

    state = secrets.token_urlsafe(24)
    metadata = {
        **(record.metadata_ or {}),
        "oauth_state": state,
        "oauth_state_expires_at": (
            datetime.now(UTC) + timedelta(minutes=META_STATE_TTL_MINUTES)
        ).isoformat(),
        "oauth_redirect_uri": redirect_uri,
    }
    record.metadata_ = metadata
    authorize_url = await meta_service.build_oauth_authorize_url(
        db,
        redirect_uri=redirect_uri,
        state=state,
    )
    await audit_service.record(
        db,
        user_id=current.id,
        action="integrations.oauth_start",
        resource_type="integration",
        resource_id="meta_app",
        metadata={"redirect_uri": redirect_uri},
        request=request,
    )
    await db.commit()
    return MetaOAuthStartResponse(
        authorize_url=authorize_url,
        redirect_uri=redirect_uri,
        state=state,
    )


@router.post("/meta_app/oauth/finish", response_model=IntegrationProvider)
async def finish_meta_oauth(
    payload: MetaOAuthFinishRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, object]:
    redirect_uri = _validate_redirect_uri(payload.redirect_uri)
    record = await integration_service.get_record(db, "meta_app")
    if record is None:
        raise HTTPException(status_code=400, detail="Meta app integratsiyasi topilmadi")

    metadata = dict(record.metadata_ or {})
    expected_state = metadata.get("oauth_state")
    expected_redirect_uri = metadata.get("oauth_redirect_uri")
    expires_at_raw = metadata.get("oauth_state_expires_at")
    if expected_state != payload.state or expected_redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="Meta OAuth state mismatch")
    try:
        expires_at = datetime.fromisoformat(str(expires_at_raw))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Meta OAuth state is invalid") from exc
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Meta OAuth state expired")

    try:
        oauth = await meta_service.exchange_oauth_code(
            db,
            code=payload.code,
            redirect_uri=redirect_uri,
        )
    except MetaError as exc:
        await integration_service.mark_verified(db, "meta_app", ok=False, error=str(exc))
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    current_credentials = await integration_service.get_credentials(db, "meta_app") or {}
    new_credentials = {
        **current_credentials,
        "user_access_token": oauth["user_access_token"],
    }
    if oauth.get("page_access_token"):
        new_credentials["page_access_token"] = oauth["page_access_token"]
    if oauth.get("page_name"):
        new_credentials["page_name"] = oauth["page_name"]

    cleaned_metadata = {
        key: value
        for key, value in metadata.items()
        if key not in {"oauth_state", "oauth_state_expires_at", "oauth_redirect_uri"}
    }
    if oauth.get("pages_count") is not None:
        cleaned_metadata["pages_count"] = int(oauth["pages_count"])
    await integration_service.upsert(
        db,
        provider="meta_app",
        credentials=new_credentials,
        user_id=current.id,
        label=record.label,
        metadata=cleaned_metadata,
    )
    await integration_service.mark_verified(db, "meta_app", ok=True)
    await audit_service.record(
        db,
        user_id=current.id,
        action="integrations.oauth_finish",
        resource_type="integration",
        resource_id="meta_app",
        metadata={"pages_count": oauth.get("pages_count")},
        request=request,
    )
    matched = await _provider_response(db, "meta_app")
    await db.commit()
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
