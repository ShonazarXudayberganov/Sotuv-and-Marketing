"""Content plan item lifecycle and AI-plan import helpers."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import Brand, ContentPlanItem, Post

PLAN_STATUSES = frozenset({"idea", "draft", "review", "approved", "scheduled", "published"})

CONTENT_PLAN_DDL = """
CREATE TABLE IF NOT EXISTS content_plans (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id      uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    post_id       uuid REFERENCES posts(id) ON DELETE SET NULL,
    platform      varchar(30) NOT NULL,
    title         varchar(200) NOT NULL,
    idea          text NOT NULL,
    goal          varchar(500),
    cta           varchar(300),
    status        varchar(20) NOT NULL DEFAULT 'idea',
    planned_at    timestamptz,
    source        varchar(30) NOT NULL DEFAULT 'manual',
    sort_order    integer NOT NULL DEFAULT 0,
    metadata      jsonb,
    created_by    uuid NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
)
"""


async def ensure_table(db: AsyncSession) -> None:
    await db.execute(text(CONTENT_PLAN_DDL))
    await db.execute(
        text("CREATE INDEX IF NOT EXISTS ix_content_plans_brand ON content_plans(brand_id)")
    )
    await db.execute(
        text("CREATE INDEX IF NOT EXISTS ix_content_plans_status ON content_plans(status)")
    )
    await db.execute(
        text("CREATE INDEX IF NOT EXISTS ix_content_plans_planned_at ON content_plans(planned_at)")
    )


def validate_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized not in PLAN_STATUSES:
        allowed = ", ".join(sorted(PLAN_STATUSES))
        raise ValueError(f"Unsupported plan status. Allowed: {allowed}")
    return normalized


async def _ensure_brand(db: AsyncSession, brand_id: UUID) -> None:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")


async def list_items(
    db: AsyncSession,
    *,
    brand_id: UUID | None = None,
    platform: str | None = None,
    status: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 200,
) -> list[ContentPlanItem]:
    await ensure_table(db)
    stmt = select(ContentPlanItem).order_by(
        ContentPlanItem.planned_at.is_(None),
        ContentPlanItem.planned_at,
        ContentPlanItem.sort_order,
        ContentPlanItem.created_at,
    )
    if brand_id is not None:
        stmt = stmt.where(ContentPlanItem.brand_id == brand_id)
    if platform:
        stmt = stmt.where(ContentPlanItem.platform == platform)
    if status:
        stmt = stmt.where(ContentPlanItem.status == validate_status(status))
    if start is not None:
        stmt = stmt.where(ContentPlanItem.planned_at >= start)
    if end is not None:
        stmt = stmt.where(ContentPlanItem.planned_at < end)
    stmt = stmt.limit(limit)
    return list((await db.execute(stmt)).scalars())


async def create_item(
    db: AsyncSession,
    *,
    brand_id: UUID,
    platform: str,
    title: str,
    idea: str,
    goal: str | None,
    cta: str | None,
    status: str,
    planned_at: datetime | None,
    source: str,
    sort_order: int,
    metadata: dict[str, Any] | None,
    user_id: UUID,
) -> ContentPlanItem:
    await ensure_table(db)
    await _ensure_brand(db, brand_id)
    if not idea.strip():
        raise ValueError("Plan idea is empty")
    item = ContentPlanItem(
        brand_id=brand_id,
        platform=platform.strip().lower(),
        title=title.strip(),
        idea=idea.strip(),
        goal=goal.strip() if goal else None,
        cta=cta.strip() if cta else None,
        status=validate_status(status),
        planned_at=planned_at,
        source=source.strip().lower(),
        sort_order=sort_order,
        metadata_=metadata,
        created_by=user_id,
    )
    db.add(item)
    await db.flush()
    return item


async def update_item(
    db: AsyncSession,
    item_id: UUID,
    *,
    platform: str | None = None,
    title: str | None = None,
    idea: str | None = None,
    goal: str | None = None,
    cta: str | None = None,
    status: str | None = None,
    planned_at: datetime | None = None,
    planned_at_set: bool = False,
    sort_order: int | None = None,
    metadata: dict[str, Any] | None = None,
    metadata_set: bool = False,
) -> ContentPlanItem | None:
    await ensure_table(db)
    item = await db.get(ContentPlanItem, item_id)
    if item is None:
        return None
    if platform is not None:
        item.platform = platform.strip().lower()
    if title is not None:
        item.title = title.strip()
    if idea is not None:
        if not idea.strip():
            raise ValueError("Plan idea is empty")
        item.idea = idea.strip()
    if goal is not None:
        item.goal = goal.strip() or None
    if cta is not None:
        item.cta = cta.strip() or None
    if status is not None:
        item.status = validate_status(status)
    if planned_at_set:
        item.planned_at = planned_at
    if sort_order is not None:
        item.sort_order = sort_order
    if metadata_set:
        item.metadata_ = metadata
    await db.flush()
    return item


async def delete_item(db: AsyncSession, item_id: UUID) -> bool:
    await ensure_table(db)
    item = await db.get(ContentPlanItem, item_id)
    if item is None:
        return False
    await db.delete(item)
    await db.flush()
    return True


def _clean_ai_line(line: str) -> str:
    cleaned = re.sub(r"^\s*(?:day|kun)\s*\d+\s*[:.)-]\s*", "", line, flags=re.I)
    cleaned = re.sub(r"^\s*\d+\s*[:.)-]\s*", "", cleaned)
    cleaned = cleaned.strip(" -\t")
    return cleaned.strip()


def _title_from_idea(idea: str) -> str:
    head = re.split(r"[.!?;|]", idea, maxsplit=1)[0].strip()
    return (head or idea.strip())[:120]


def parse_plan_lines(text_value: str, *, max_items: int = 60) -> list[str]:
    lines: list[str] = []
    for raw in text_value.splitlines():
        cleaned = _clean_ai_line(raw)
        if len(cleaned) < 8:
            continue
        lowered = cleaned.lower()
        if lowered.startswith(("format:", "goal:", "cta:", "platform:", "language:")):
            continue
        lines.append(cleaned)
        if len(lines) >= max_items:
            break
    if lines:
        return lines

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text_value) if part.strip()]
    return sentences[:max_items]


async def import_text(
    db: AsyncSession,
    *,
    brand_id: UUID,
    platform: str,
    topic: str | None,
    text_value: str,
    start_date: date,
    user_id: UUID,
) -> list[ContentPlanItem]:
    await ensure_table(db)
    await _ensure_brand(db, brand_id)
    ideas = parse_plan_lines(text_value)
    if not ideas:
        raise ValueError("No plan items found in text")

    start_dt = datetime.combine(start_date, time(hour=9), tzinfo=UTC)
    items: list[ContentPlanItem] = []
    for index, idea in enumerate(ideas):
        item = ContentPlanItem(
            brand_id=brand_id,
            platform=platform.strip().lower(),
            title=_title_from_idea(idea),
            idea=idea,
            goal=topic.strip()[:500] if topic else None,
            cta=None,
            status="idea",
            planned_at=start_dt + timedelta(days=index),
            source="ai_import",
            sort_order=index,
            metadata_={"topic": topic, "imported_from": "ai_text"},
            created_by=user_id,
        )
        db.add(item)
        items.append(item)
    await db.flush()
    return items


async def create_post_from_item(
    db: AsyncSession,
    item_id: UUID,
    *,
    social_account_ids: Sequence[UUID],
    scheduled_at: datetime | None,
    user_id: UUID,
) -> tuple[ContentPlanItem, Post] | None:
    await ensure_table(db)
    item = await db.get(ContentPlanItem, item_id)
    if item is None:
        return None
    body_parts = [item.idea]
    if item.cta:
        body_parts.append(item.cta)
    from app.services import post_service

    post = await post_service.create_post(
        db,
        brand_id=item.brand_id,
        body="\n\n".join(body_parts),
        title=item.title,
        media_urls=None,
        social_account_ids=social_account_ids,
        scheduled_at=scheduled_at,
        user_id=user_id,
    )
    item.post_id = post.id
    item.status = "scheduled" if scheduled_at is not None else "draft"
    await db.flush()
    return item, post


__all__ = [
    "PLAN_STATUSES",
    "create_item",
    "create_post_from_item",
    "delete_item",
    "ensure_table",
    "import_text",
    "list_items",
    "parse_plan_lines",
    "update_item",
    "validate_status",
]
