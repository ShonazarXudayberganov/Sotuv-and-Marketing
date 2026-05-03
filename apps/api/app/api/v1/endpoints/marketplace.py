from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.marketplace import (
    TestDeliveryRequest,
    WebhookDeliveryOut,
    WebhookEndpointCreate,
    WebhookEndpointOut,
    WebhookEndpointWithSecret,
)
from app.services import audit_service, sync_service, webhook_service
from app.services.integration_service import PROVIDERS

router = APIRouter()


@router.get("/catalog")
async def catalog(
    _: CurrentUser = Depends(require_permission("integrations.read")),
) -> list[dict[str, Any]]:
    """All known integration providers (catalog metadata only — no creds)."""
    out: list[dict[str, Any]] = []
    for key, spec in PROVIDERS.items():
        out.append(
            {
                "provider": key,
                "label": spec["label"],
                "category": spec["category"],
                "description": spec["description"],
                "secret_fields": spec["secret_fields"],
                "docs_url": spec.get("docs_url"),
            }
        )
    return out


# ─────────── Webhook endpoints ───────────


@router.get("/webhooks", response_model=list[WebhookEndpointOut])
async def list_webhooks(
    direction: str | None = None,
    _: CurrentUser = Depends(require_permission("integrations.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[WebhookEndpointOut]:
    rows = await webhook_service.list_endpoints(db, direction=direction)
    return [WebhookEndpointOut.model_validate(r) for r in rows]


@router.post("/webhooks", response_model=WebhookEndpointWithSecret, status_code=201)
async def create_webhook(
    payload: WebhookEndpointCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> WebhookEndpointWithSecret:
    try:
        rec = await webhook_service.create_endpoint(
            db,
            name=payload.name,
            direction=payload.direction,
            url=payload.url,
            events=payload.events,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await audit_service.record(
        db,
        user_id=current.id,
        action="webhooks.create",
        resource_type="webhook",
        resource_id=str(rec.id),
        request=request,
    )
    response = WebhookEndpointWithSecret.model_validate(rec)
    await db.commit()
    return response


@router.post("/webhooks/{eid}/rotate-secret", response_model=WebhookEndpointWithSecret)
async def rotate_secret(
    eid: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> WebhookEndpointWithSecret:
    rec = await webhook_service.rotate_secret(db, eid)
    if rec is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="webhooks.rotate",
        resource_type="webhook",
        resource_id=str(eid),
        request=request,
    )
    response = WebhookEndpointWithSecret.model_validate(rec)
    await db.commit()
    return response


@router.post("/webhooks/{eid}/toggle", response_model=WebhookEndpointOut)
async def toggle_webhook(
    eid: UUID,
    active: bool = True,
    _: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> WebhookEndpointOut:
    rec = await webhook_service.set_active(db, eid, active=active)
    if rec is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    response = WebhookEndpointOut.model_validate(rec)
    await db.commit()
    return response


@router.post("/webhooks/{eid}/test", response_model=WebhookDeliveryOut)
async def test_webhook(
    eid: UUID,
    payload: TestDeliveryRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> WebhookDeliveryOut:
    ep = await webhook_service.get_endpoint(db, eid)
    if ep is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    if ep.direction != "out":
        raise HTTPException(status_code=400, detail="Only outbound webhooks can be tested")
    count = await webhook_service.deliver_outbound(db, event=payload.event, payload=payload.payload)
    if count == 0:
        raise HTTPException(status_code=400, detail="No matching active outbound endpoint")
    await audit_service.record(
        db,
        user_id=current.id,
        action="webhooks.test",
        resource_type="webhook",
        resource_id=str(eid),
        request=request,
    )
    deliveries = await webhook_service.list_deliveries(db, endpoint_id=eid, limit=1)
    if not deliveries:
        raise HTTPException(status_code=500, detail="Delivery not recorded")
    response = WebhookDeliveryOut.model_validate(deliveries[0])
    await db.commit()
    return response


@router.delete("/webhooks/{eid}")
async def delete_webhook(
    eid: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await webhook_service.delete_endpoint(db, eid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="webhooks.delete",
        resource_type="webhook",
        resource_id=str(eid),
        request=request,
    )
    await db.commit()
    return {"deleted": True}


@router.get("/webhooks/{eid}/deliveries", response_model=list[WebhookDeliveryOut])
async def deliveries(
    eid: UUID,
    limit: int = 50,
    _: CurrentUser = Depends(require_permission("integrations.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[WebhookDeliveryOut]:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    rows = await webhook_service.list_deliveries(db, endpoint_id=eid, limit=limit)
    return [WebhookDeliveryOut.model_validate(r) for r in rows]


@router.post("/sync/{provider}")
async def run_sync(
    provider: str,
    request: Request,
    current: CurrentUser = Depends(require_permission("integrations.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, Any]:
    try:
        result = await sync_service.run_sync(db, provider=provider, user_id=current.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await audit_service.record(
        db,
        user_id=current.id,
        action="marketplace.sync",
        resource_type="integration",
        resource_id=provider,
        metadata={
            "pulled": result.pulled,
            "pushed": result.pushed,
            "mocked": result.mocked,
        },
        request=request,
    )
    await db.commit()
    return result.to_dict()


@router.post("/webhooks/in/{eid}", status_code=200)
async def receive_inbound(
    eid: UUID,
    request: Request,
    x_nexus_signature: str | None = Header(default=None),
    x_nexus_event: str | None = Header(default=None),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, Any]:
    """Inbound endpoint — verifies HMAC and records the payload.

    Public endpoint inside the tenant scope; the JWT provides tenancy isolation
    while the HMAC ensures only the registered partner can post.
    """
    ep = await webhook_service.get_endpoint(db, eid)
    if ep is None or ep.direction != "in":
        raise HTTPException(status_code=404, detail="Webhook not found")
    if not ep.is_active:
        raise HTTPException(status_code=403, detail="Webhook is inactive")
    raw = await request.body()
    delivery = await webhook_service.record_inbound(
        db,
        endpoint=ep,
        raw=raw,
        signature=x_nexus_signature,
        event=x_nexus_event,
    )
    await db.commit()
    if not delivery.succeeded:
        raise HTTPException(status_code=401, detail=delivery.error or "Invalid signature")
    return {"received": True, "delivery_id": str(delivery.id)}
