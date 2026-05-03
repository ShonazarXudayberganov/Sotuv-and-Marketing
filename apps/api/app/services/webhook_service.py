"""Webhook lifecycle: HMAC verification, outbound delivery, audit log."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import WebhookDelivery, WebhookEndpoint

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
SUPPORTED_EVENTS = (
    "contact.created",
    "contact.updated",
    "deal.created",
    "deal.won",
    "deal.lost",
    "post.published",
    "ads.snapshot",
    "inbox.message_in",
)


def _is_mock_mode() -> bool:
    return os.getenv("WEBHOOK_MOCK", "false").lower() in {"1", "true", "yes"}


def generate_secret() -> str:
    return secrets.token_urlsafe(32)


def sign(secret: str, body: bytes) -> str:
    """HMAC-SHA256 signature in hex (X-Nexus-Signature header)."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify(secret: str, body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = sign(secret, body)
    return hmac.compare_digest(expected, signature)


# ─────────── Endpoint CRUD ───────────


async def list_endpoints(
    db: AsyncSession, *, direction: str | None = None
) -> list[WebhookEndpoint]:
    stmt = select(WebhookEndpoint).order_by(desc(WebhookEndpoint.updated_at))
    if direction is not None:
        stmt = stmt.where(WebhookEndpoint.direction == direction)
    return list((await db.execute(stmt)).scalars())


async def get_endpoint(db: AsyncSession, eid: UUID) -> WebhookEndpoint | None:
    return await db.get(WebhookEndpoint, eid)


async def create_endpoint(
    db: AsyncSession,
    *,
    name: str,
    direction: str,
    url: str | None,
    events: list[str] | None,
    user_id: UUID,
) -> WebhookEndpoint:
    if direction not in {"in", "out"}:
        raise ValueError("direction must be 'in' or 'out'")
    if direction == "out" and not url:
        raise ValueError("Outbound webhook requires a URL")
    if events:
        unknown = [e for e in events if e not in SUPPORTED_EVENTS]
        if unknown:
            raise ValueError(f"Unknown events: {', '.join(unknown)}")
    rec = WebhookEndpoint(
        name=name.strip(),
        direction=direction,
        url=url,
        secret=generate_secret(),
        events=events,
        created_by=user_id,
    )
    db.add(rec)
    await db.flush()
    return rec


async def rotate_secret(db: AsyncSession, eid: UUID) -> WebhookEndpoint | None:
    rec = await db.get(WebhookEndpoint, eid)
    if rec is None:
        return None
    rec.secret = generate_secret()
    await db.flush()
    return rec


async def set_active(
    db: AsyncSession, eid: UUID, *, active: bool
) -> WebhookEndpoint | None:
    rec = await db.get(WebhookEndpoint, eid)
    if rec is None:
        return None
    rec.is_active = active
    await db.flush()
    return rec


async def delete_endpoint(db: AsyncSession, eid: UUID) -> bool:
    rec = await db.get(WebhookEndpoint, eid)
    if rec is None:
        return False
    await db.delete(rec)
    await db.flush()
    return True


# ─────────── Inbound ───────────


async def record_inbound(
    db: AsyncSession,
    *,
    endpoint: WebhookEndpoint,
    raw: bytes,
    signature: str | None,
    event: str | None,
) -> WebhookDelivery:
    valid = verify(endpoint.secret, raw, signature)
    delivery = WebhookDelivery(
        endpoint_id=endpoint.id,
        direction="in",
        event=event,
        status_code=200 if valid else 401,
        request_body=raw.decode("utf-8", errors="ignore")[:5000],
        attempts=1,
        succeeded=valid,
        error=None if valid else "Invalid HMAC signature",
    )
    db.add(delivery)
    endpoint.last_triggered_at = datetime.now(UTC)
    endpoint.last_status = delivery.status_code
    if valid:
        endpoint.success_count += 1
        endpoint.last_error = None
    else:
        endpoint.failure_count += 1
        endpoint.last_error = "Invalid HMAC"
    await db.flush()
    return delivery


# ─────────── Outbound ───────────


async def deliver_outbound(
    db: AsyncSession, *, event: str, payload: dict[str, Any]
) -> int:
    """Fire all active outbound endpoints subscribed to ``event``.

    Returns the number of attempted deliveries. Each attempt is recorded.
    """
    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.direction == "out", WebhookEndpoint.is_active.is_(True)
    )
    endpoints = list((await db.execute(stmt)).scalars())
    targets = [
        e for e in endpoints if not e.events or event in (e.events or [])
    ]
    if not targets:
        return 0
    body = json.dumps(
        {"event": event, "payload": payload, "ts": datetime.now(UTC).isoformat()}
    ).encode()
    for ep in targets:
        await _deliver_one(db, ep, event, body)
    return len(targets)


async def _deliver_one(
    db: AsyncSession,
    endpoint: WebhookEndpoint,
    event: str,
    body: bytes,
) -> WebhookDelivery:
    headers = {
        "Content-Type": "application/json",
        "X-Nexus-Event": event,
        "X-Nexus-Signature": sign(endpoint.secret, body),
    }
    status = 0
    response_body = ""
    error: str | None = None
    success = False
    if _is_mock_mode() or not endpoint.url:
        status = 200
        response_body = '{"mock": true}'
        success = True
    else:
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as http:
                resp = await http.post(endpoint.url, content=body, headers=headers)
            status = resp.status_code
            response_body = resp.text[:2000]
            success = 200 <= resp.status_code < 300
        except httpx.HTTPError as exc:
            error = str(exc)[:500]
    delivery = WebhookDelivery(
        endpoint_id=endpoint.id,
        direction="out",
        event=event,
        status_code=status if status else None,
        request_body=body.decode("utf-8", errors="ignore")[:5000],
        response_body=response_body,
        attempts=1,
        succeeded=success,
        error=error,
    )
    db.add(delivery)
    endpoint.last_triggered_at = datetime.now(UTC)
    endpoint.last_status = status if status else None
    if success:
        endpoint.success_count += 1
        endpoint.last_error = None
    else:
        endpoint.failure_count += 1
        endpoint.last_error = error or f"HTTP {status}"
    await db.flush()
    return delivery


# ─────────── Audit log ───────────


async def list_deliveries(
    db: AsyncSession, *, endpoint_id: UUID | None = None, limit: int = 50
) -> list[WebhookDelivery]:
    stmt = select(WebhookDelivery).order_by(desc(WebhookDelivery.created_at)).limit(limit)
    if endpoint_id is not None:
        stmt = stmt.where(WebhookDelivery.endpoint_id == endpoint_id)
    return list((await db.execute(stmt)).scalars())


__all__ = [
    "SUPPORTED_EVENTS",
    "create_endpoint",
    "delete_endpoint",
    "deliver_outbound",
    "generate_secret",
    "get_endpoint",
    "list_deliveries",
    "list_endpoints",
    "record_inbound",
    "rotate_secret",
    "set_active",
    "sign",
    "verify",
]
