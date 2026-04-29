from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.core.security import InvalidTokenError, decode_token
from app.core.tenancy import validate_schema_name
from app.models.tenant_scoped import Notification
from app.services.notification_service import broker

router = APIRouter()


@router.get("")
async def list_notifications(
    current: CurrentUser = Depends(require_permission("notifications.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[dict[str, object]]:
    rows = (
        await db.execute(
            select(Notification)
            .where(Notification.user_id == current.id)
            .order_by(Notification.created_at.desc())
            .limit(50)
        )
    ).scalars()
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "body": n.body,
            "category": n.category,
            "severity": n.severity,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in rows
    ]


@router.post("/mark-all-read")
async def mark_all_read(
    current: CurrentUser = Depends(require_permission("notifications.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, int]:
    rows = (
        await db.execute(
            select(Notification).where(
                Notification.user_id == current.id, Notification.read_at.is_(None)
            )
        )
    ).scalars()
    now = datetime.now(UTC)
    count = 0
    for note in rows:
        note.read_at = now
        count += 1
    await db.commit()
    return {"marked": count}


@router.websocket("/ws")
async def ws_notifications(websocket: WebSocket) -> None:
    """Token-via-query-string WebSocket. Subscribes the caller to broker events."""
    token = websocket.query_params.get("token", "")
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        await websocket.close(code=4401)
        return

    if payload.get("type") != "access":
        await websocket.close(code=4401)
        return

    try:
        schema = validate_schema_name(payload.get("tenant_schema", ""))
    except ValueError:
        await websocket.close(code=4401)
        return

    user_id = payload.get("sub", "")
    await websocket.accept()
    queue = await broker.subscribe(schema, user_id)

    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_text(message)
            except TimeoutError:
                await websocket.send_text('{"type":"ping"}')
    except WebSocketDisconnect:
        pass
    finally:
        await broker.unsubscribe(schema, user_id, queue)
