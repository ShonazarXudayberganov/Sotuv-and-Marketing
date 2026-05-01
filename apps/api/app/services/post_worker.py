"""APScheduler-driven sweep that publishes due posts.

Runs every 30 seconds (configurable via POST_WORKER_INTERVAL_SECONDS env).
Iterates every tenant schema, claims due rows atomically, and publishes
each one. Disabled when POST_WORKER_DISABLED=true (used by tests so they
can drive publish_now() deterministically).
"""

from __future__ import annotations

import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, text

from app.core.db import get_session_factory
from app.core.tenancy import validate_schema_name
from app.models.tenant import Tenant
from app.services import post_service

logger = logging.getLogger(__name__)

INTERVAL_SECONDS = int(os.getenv("POST_WORKER_INTERVAL_SECONDS", "30"))
_scheduler: AsyncIOScheduler | None = None


def is_disabled() -> bool:
    return os.getenv("POST_WORKER_DISABLED", "false").lower() in {"1", "true", "yes"}


async def _list_tenant_schemas() -> list[str]:
    factory = get_session_factory()
    async with factory() as session:
        rows = (await session.execute(select(Tenant.schema_name))).scalars().all()
    return [s for s in rows if s]


async def _process_schema(schema: str) -> None:
    safe = validate_schema_name(schema)
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(text(f"SET search_path TO {safe}, public"))
        due = await post_service.claim_due_posts(session)
        if not due:
            await session.commit()
            return
        logger.info("Worker[%s]: claimed %d post(s) for publishing", safe, len(due))
        for post in due:
            try:
                await post_service.publish_now(session, post)
            except Exception:
                logger.exception("Worker[%s]: publish_now crashed for %s", safe, post.id)
                post.status = "failed"
                post.last_error = "Worker exception — see logs"
        await session.commit()


async def sweep_once() -> None:
    """Single sweep across all tenants — also exposed for manual triggering in tests."""
    if is_disabled():
        return
    schemas = await _list_tenant_schemas()
    for schema in schemas:
        try:
            await _process_schema(schema)
        except Exception:
            logger.exception("Worker: tenant sweep failed for %s", schema)


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    if is_disabled():
        logger.info("Post worker disabled (POST_WORKER_DISABLED=true)")
        return None
    if _scheduler is not None:
        return _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        sweep_once,
        "interval",
        seconds=INTERVAL_SECONDS,
        id="posts.sweep",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("Post worker started — interval=%ds", INTERVAL_SECONDS)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


__all__ = ["is_disabled", "start_scheduler", "stop_scheduler", "sweep_once"]
