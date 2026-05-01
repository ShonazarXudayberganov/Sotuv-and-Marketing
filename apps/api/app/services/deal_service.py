"""CRM deals + multi-pipeline lifecycle.

A deal lives inside a pipeline stage; moving stages auto-syncs probability
to the stage default (the user can override). Winning/losing closes the
deal and writes a status_change activity onto the linked contact.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Contact, ContactActivity, Deal, Pipeline, PipelineStage

# ─────────── Pipelines ───────────


async def list_pipelines(db: AsyncSession) -> list[Pipeline]:
    stmt = select(Pipeline).where(Pipeline.is_active.is_(True)).order_by(
        Pipeline.sort_order, Pipeline.name
    )
    return list((await db.execute(stmt)).scalars())


async def get_pipeline(db: AsyncSession, pipeline_id: UUID) -> Pipeline | None:
    return await db.get(Pipeline, pipeline_id)


async def list_stages(db: AsyncSession, pipeline_id: UUID) -> list[PipelineStage]:
    stmt = (
        select(PipelineStage)
        .where(PipelineStage.pipeline_id == pipeline_id)
        .order_by(asc(PipelineStage.sort_order))
    )
    return list((await db.execute(stmt)).scalars())


async def default_pipeline(db: AsyncSession) -> Pipeline | None:
    stmt = (
        select(Pipeline)
        .where(Pipeline.is_default.is_(True), Pipeline.is_active.is_(True))
        .limit(1)
    )
    return (await db.execute(stmt)).scalars().first()


# ─────────── Deals ───────────


async def list_deals(
    db: AsyncSession,
    *,
    pipeline_id: UUID | None = None,
    stage_id: UUID | None = None,
    contact_id: UUID | None = None,
    assignee_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[Deal]:
    stmt = (
        select(Deal)
        .order_by(desc(Deal.updated_at))
        .limit(limit)
    )
    conds = []
    if pipeline_id is not None:
        conds.append(Deal.pipeline_id == pipeline_id)
    if stage_id is not None:
        conds.append(Deal.stage_id == stage_id)
    if contact_id is not None:
        conds.append(Deal.contact_id == contact_id)
    if assignee_id is not None:
        conds.append(Deal.assignee_id == assignee_id)
    if status is not None:
        conds.append(Deal.status == status)
    if conds:
        stmt = stmt.where(and_(*conds))
    return list((await db.execute(stmt)).scalars())


async def get_deal(db: AsyncSession, deal_id: UUID) -> Deal | None:
    return await db.get(Deal, deal_id)


async def _resolve_default_stage(
    db: AsyncSession, pipeline_id: UUID
) -> PipelineStage | None:
    stages = await list_stages(db, pipeline_id)
    return stages[0] if stages else None


async def create_deal(
    db: AsyncSession,
    *,
    title: str,
    contact_id: UUID | None,
    pipeline_id: UUID | None,
    stage_id: UUID | None,
    amount: int,
    currency: str,
    expected_close_at: datetime | None,
    assignee_id: UUID | None,
    department_id: UUID | None,
    notes: str | None,
    tags: list[str] | None,
    user_id: UUID,
) -> Deal:
    if not title.strip():
        raise ValueError("Deal title is empty")

    # Resolve pipeline (fall back to default)
    pipeline: Pipeline | None
    if pipeline_id is not None:
        pipeline = await db.get(Pipeline, pipeline_id)
        if pipeline is None:
            raise ValueError("Pipeline not found")
    else:
        pipeline = await default_pipeline(db)
        if pipeline is None:
            raise ValueError("No pipeline configured")

    # Resolve stage (fall back to first stage of the pipeline)
    stage: PipelineStage | None
    if stage_id is not None:
        stage = await db.get(PipelineStage, stage_id)
        if stage is None or stage.pipeline_id != pipeline.id:
            raise ValueError("Stage does not belong to this pipeline")
    else:
        stage = await _resolve_default_stage(db, pipeline.id)
        if stage is None:
            raise ValueError("Pipeline has no stages")

    if contact_id is not None:
        contact = await db.get(Contact, contact_id)
        if contact is None:
            raise ValueError("Contact not found")

    deal = Deal(
        title=title.strip(),
        contact_id=contact_id,
        pipeline_id=pipeline.id,
        stage_id=stage.id,
        amount=max(0, int(amount)),
        currency=(currency or "UZS").upper()[:3],
        probability=stage.default_probability,
        status="open",
        expected_close_at=expected_close_at,
        assignee_id=assignee_id,
        department_id=department_id,
        notes=notes,
        tags=tags,
        created_by=user_id,
    )
    db.add(deal)
    await db.flush()

    if contact_id is not None:
        await _log_activity(
            db,
            contact_id=contact_id,
            kind="status_change",
            title="Yangi bitim yaratildi",
            body=f"{deal.title} — {stage.name}",
            user_id=user_id,
        )
    return deal


async def update_deal(
    db: AsyncSession,
    deal_id: UUID,
    *,
    payload: dict[str, Any],
    user_id: UUID,
) -> Deal | None:
    deal = await db.get(Deal, deal_id)
    if deal is None:
        return None

    stage_changed = False
    if payload.get("stage_id"):
        new_stage_id = payload["stage_id"]
        if new_stage_id != deal.stage_id:
            stage = await db.get(PipelineStage, new_stage_id)
            if stage is None or stage.pipeline_id != deal.pipeline_id:
                raise ValueError("Stage does not belong to this pipeline")
            deal.stage_id = stage.id
            deal.probability = stage.default_probability
            if stage.is_won:
                deal.status = "won"
                deal.is_won = True
                deal.closed_at = datetime.now(UTC)
            elif stage.is_lost:
                deal.status = "lost"
                deal.is_won = False
                deal.closed_at = datetime.now(UTC)
            else:
                deal.status = "open"
                deal.is_won = False
                deal.closed_at = None
            stage_changed = True

    for field in (
        "title",
        "contact_id",
        "amount",
        "currency",
        "probability",
        "expected_close_at",
        "department_id",
        "assignee_id",
        "notes",
        "tags",
        "sort_order",
    ):
        if field in payload:
            setattr(deal, field, payload[field])

    await db.flush()

    if stage_changed and deal.contact_id is not None:
        stage = await db.get(PipelineStage, deal.stage_id)
        await _log_activity(
            db,
            contact_id=deal.contact_id,
            kind="status_change",
            title="Bitim bosqichi o'zgardi",
            body=f"{deal.title} → {stage.name if stage else '—'}",
            user_id=user_id,
        )
    return deal


async def win_deal(db: AsyncSession, deal_id: UUID, *, user_id: UUID) -> Deal | None:
    deal = await db.get(Deal, deal_id)
    if deal is None:
        return None
    stages = await list_stages(db, deal.pipeline_id)
    won_stage = next((s for s in stages if s.is_won), None)
    if won_stage is None:
        raise ValueError("Pipeline has no won stage")
    return await update_deal(
        db, deal_id, payload={"stage_id": won_stage.id}, user_id=user_id
    )


async def lose_deal(db: AsyncSession, deal_id: UUID, *, user_id: UUID) -> Deal | None:
    deal = await db.get(Deal, deal_id)
    if deal is None:
        return None
    stages = await list_stages(db, deal.pipeline_id)
    lost_stage = next((s for s in stages if s.is_lost), None)
    if lost_stage is None:
        raise ValueError("Pipeline has no lost stage")
    return await update_deal(
        db, deal_id, payload={"stage_id": lost_stage.id}, user_id=user_id
    )


async def delete_deal(db: AsyncSession, deal_id: UUID) -> bool:
    deal = await db.get(Deal, deal_id)
    if deal is None:
        return False
    await db.delete(deal)
    await db.flush()
    return True


# ─────────── Forecast / stats ───────────


async def forecast(
    db: AsyncSession, *, pipeline_id: UUID | None = None
) -> dict[str, Any]:
    """Probability-weighted total of OPEN deals plus straight totals."""
    stmt = select(Deal).where(Deal.status == "open")
    if pipeline_id is not None:
        stmt = stmt.where(Deal.pipeline_id == pipeline_id)
    rows = list((await db.execute(stmt)).scalars())
    raw_total = sum(d.amount for d in rows)
    weighted = sum(int(d.amount * d.probability / 100) for d in rows)
    by_stage: dict[str, dict[str, int]] = {}
    for d in rows:
        slot = by_stage.setdefault(str(d.stage_id), {"count": 0, "amount": 0})
        slot["count"] += 1
        slot["amount"] += d.amount
    return {
        "open_count": len(rows),
        "open_amount": raw_total,
        "weighted_amount": weighted,
        "by_stage": by_stage,
    }


async def stats(db: AsyncSession) -> dict[str, Any]:
    rows = list((await db.execute(select(Deal))).scalars())
    by_status: dict[str, int] = {}
    won_amount = 0
    lost_amount = 0
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        if r.status == "won":
            won_amount += r.amount
        elif r.status == "lost":
            lost_amount += r.amount
    closed = by_status.get("won", 0) + by_status.get("lost", 0)
    win_rate = (by_status.get("won", 0) / closed) if closed else 0.0
    return {
        "total": len(rows),
        "by_status": by_status,
        "won_amount": won_amount,
        "lost_amount": lost_amount,
        "win_rate": round(win_rate, 4),
    }


# ─────────── Helpers ───────────


async def _log_activity(
    db: AsyncSession,
    *,
    contact_id: UUID,
    kind: str,
    title: str,
    body: str | None,
    user_id: UUID | None,
) -> None:
    db.add(
        ContactActivity(
            contact_id=contact_id,
            kind=kind,
            title=title,
            body=body,
            occurred_at=datetime.now(UTC),
            created_by=user_id,
        )
    )
    await db.flush()


__all__ = [
    "create_deal",
    "default_pipeline",
    "delete_deal",
    "forecast",
    "get_deal",
    "get_pipeline",
    "list_deals",
    "list_pipelines",
    "list_stages",
    "lose_deal",
    "stats",
    "update_deal",
    "win_deal",
]
