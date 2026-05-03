"""Notification persistence + in-process pub/sub.

Sprint 4 ships an in-memory broker (asyncio Queues per (tenant, user)). Sprint 5
will swap this for Redis pub/sub when we deploy multi-instance.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant_scoped import Notification, NotificationPreference

DEFAULT_PREFERENCES: dict[str, list[str]] = {
    "tasks": ["in_app", "email"],
    "billing": ["in_app", "email"],
    "ai": ["in_app"],
    "inbox": ["in_app", "telegram"],
    "social": ["in_app"],
    "system": ["in_app", "email"],
}


class _Broker:
    def __init__(self) -> None:
        self._subscribers: dict[tuple[str, str], list[asyncio.Queue[str]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, tenant_schema: str, user_id: str) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[(tenant_schema, user_id)].append(queue)
        return queue

    async def unsubscribe(
        self, tenant_schema: str, user_id: str, queue: asyncio.Queue[str]
    ) -> None:
        async with self._lock:
            subs = self._subscribers.get((tenant_schema, user_id), [])
            if queue in subs:
                subs.remove(queue)

    async def publish(self, tenant_schema: str, user_id: str, payload: dict[str, Any]) -> None:
        message = json.dumps(payload, default=str)
        async with self._lock:
            subs = list(self._subscribers.get((tenant_schema, user_id), []))
        for queue in subs:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass


broker = _Broker()


async def create_and_push(
    db: AsyncSession,
    *,
    tenant_schema: str,
    user_id: UUID,
    title: str,
    body: str | None = None,
    category: str = "system",
    severity: str = "info",
    payload: dict[str, Any] | None = None,
) -> Notification:
    note = Notification(
        user_id=user_id,
        title=title,
        body=body,
        category=category,
        severity=severity,
        payload=payload,
    )
    db.add(note)
    await db.flush()

    await broker.publish(
        tenant_schema,
        str(user_id),
        {
            "type": "notification",
            "id": str(note.id),
            "title": title,
            "body": body,
            "category": category,
            "severity": severity,
            "created_at": note.created_at.isoformat() if note.created_at else None,
        },
    )
    return note


async def get_preferences(db: AsyncSession, user_id: UUID) -> NotificationPreference:
    """Return the user's preferences row, creating it with defaults if absent."""
    pref = (
        await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
    ).scalar_one_or_none()
    if pref is None:
        pref = NotificationPreference(
            user_id=user_id,
            channels=dict(DEFAULT_PREFERENCES),
        )
        db.add(pref)
        await db.flush()
    return pref


async def update_preferences(
    db: AsyncSession,
    user_id: UUID,
    *,
    channels: dict[str, list[str]] | None = None,
    quiet_hours_start: int | None = None,
    quiet_hours_end: int | None = None,
    telegram_chat_id: str | None = None,
    update_quiet: bool = False,
    update_telegram: bool = False,
) -> NotificationPreference:
    pref = await get_preferences(db, user_id)
    if channels is not None:
        merged = dict(pref.channels)
        merged.update(channels)
        pref.channels = merged
    if update_quiet:
        pref.quiet_hours_start = quiet_hours_start
        pref.quiet_hours_end = quiet_hours_end
    if update_telegram:
        pref.telegram_chat_id = telegram_chat_id
    return pref
