"""CRM contact lifecycle: CRUD, search, activity timeline, AI score."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Contact, ContactActivity

# ─────────── Score heuristic ───────────

ENGAGEMENT_KIND_WEIGHT = {
    "call_in": 12,
    "call_out": 8,
    "message_in": 10,
    "message_out": 6,
    "email": 4,
    "meeting": 18,
    "task": 2,
    "note": 1,
    "status_change": 0,
}


def _recency_bonus(occurred_at: datetime, now: datetime) -> int:
    """Decay: same day = full 10 pts, halves every 7 days, floor 0."""
    age = (now - occurred_at).total_seconds() / 86400  # days
    if age <= 1:
        return 10
    if age <= 7:
        return 6
    if age <= 30:
        return 3
    return 0


def compute_score(
    contact: Contact, activities: Sequence[ContactActivity]
) -> tuple[int, str]:
    """Returns (score 0..100, human-readable reason).

    Pure function — easy to test, no DB or AI calls. The AI-driven version
    is wired in score_with_ai() below for tenants with credits.
    """
    now = datetime.now(UTC)
    score = 0

    # Base from status
    score += {
        "lead": 10,
        "active": 35,
        "customer": 70,
        "lost": 0,
        "archived": 0,
    }.get(contact.status, 5)

    # Has any contact channel?
    channels = sum(
        bool(v)
        for v in (
            contact.phone,
            contact.email,
            contact.telegram_username,
            contact.instagram_username,
        )
    )
    score += min(channels * 5, 15)

    # Engagement from recent activities (cap at 50)
    eng = 0
    for act in activities[:30]:  # consider last 30 only
        weight = ENGAGEMENT_KIND_WEIGHT.get(act.kind, 0)
        eng += weight + _recency_bonus(act.occurred_at, now)
    score += min(eng, 50)

    # Tag bumps
    tags = set(contact.tags or [])
    if "vip" in tags:
        score += 10
    if "cold" in tags:
        score -= 10

    score = max(0, min(100, score))

    if score >= 75:
        reason = "Yuqori faollik va to'liq aloqa kanallari"
    elif score >= 45:
        reason = "O'rtacha qiziqish — keyingi qadamni rejalashtiring"
    elif score >= 20:
        reason = "Past faollik — qayta qiziqtirish kerak"
    else:
        reason = "Sovuq — yangi tegmaslar bilan boshlang"
    return score, reason


# ─────────── CRUD ───────────


async def list_contacts(
    db: AsyncSession,
    *,
    query: str | None = None,
    status: str | None = None,
    department_id: UUID | None = None,
    min_score: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Contact]:
    stmt = select(Contact).order_by(desc(Contact.ai_score), desc(Contact.updated_at))
    conds = []
    if status is not None:
        conds.append(Contact.status == status)
    if department_id is not None:
        conds.append(Contact.department_id == department_id)
    if min_score is not None:
        conds.append(Contact.ai_score >= min_score)
    if query:
        like = f"%{query.strip()}%"
        conds.append(
            or_(
                Contact.full_name.ilike(like),
                Contact.company_name.ilike(like),
                Contact.phone.ilike(like),
                Contact.email.ilike(like),
            )
        )
    if conds:
        stmt = stmt.where(and_(*conds))
    stmt = stmt.limit(limit).offset(offset)
    return list((await db.execute(stmt)).scalars())


async def get_contact(db: AsyncSession, contact_id: UUID) -> Contact | None:
    return await db.get(Contact, contact_id)


async def create_contact(
    db: AsyncSession,
    *,
    payload: dict[str, Any],
    user_id: UUID,
) -> Contact:
    if not (payload.get("full_name") or "").strip():
        raise ValueError("full_name is required")
    contact = Contact(
        full_name=payload["full_name"].strip(),
        company_name=payload.get("company_name"),
        phone=payload.get("phone"),
        email=payload.get("email"),
        telegram_username=payload.get("telegram_username"),
        instagram_username=payload.get("instagram_username"),
        industry=payload.get("industry"),
        source=payload.get("source"),
        status=payload.get("status") or "lead",
        department_id=payload.get("department_id"),
        assignee_id=payload.get("assignee_id"),
        notes=payload.get("notes"),
        custom_fields=payload.get("custom_fields"),
        tags=payload.get("tags"),
        created_by=user_id,
    )
    score, reason = compute_score(contact, [])
    contact.ai_score = score
    contact.ai_score_reason = reason
    contact.ai_score_updated_at = datetime.now(UTC)
    db.add(contact)
    await db.flush()
    from app.services import webhook_service

    await webhook_service.fire_event(
        db,
        event="contact.created",
        payload={
            "id": str(contact.id),
            "full_name": contact.full_name,
            "phone": contact.phone,
            "email": contact.email,
            "status": contact.status,
            "ai_score": contact.ai_score,
        },
    )
    return contact


async def update_contact(
    db: AsyncSession,
    contact_id: UUID,
    *,
    payload: dict[str, Any],
) -> Contact | None:
    contact = await db.get(Contact, contact_id)
    if contact is None:
        return None
    for field in (
        "full_name",
        "company_name",
        "phone",
        "email",
        "telegram_username",
        "instagram_username",
        "industry",
        "source",
        "status",
        "department_id",
        "assignee_id",
        "notes",
        "custom_fields",
        "tags",
    ):
        if field in payload:
            setattr(contact, field, payload[field])
    activities = await list_activities(db, contact_id, limit=30)
    score, reason = compute_score(contact, activities)
    contact.ai_score = score
    contact.ai_score_reason = reason
    contact.ai_score_updated_at = datetime.now(UTC)
    await db.flush()
    return contact


async def delete_contact(db: AsyncSession, contact_id: UUID) -> bool:
    contact = await db.get(Contact, contact_id)
    if contact is None:
        return False
    await db.delete(contact)
    await db.flush()
    return True


# ─────────── Activities ───────────


async def list_activities(
    db: AsyncSession,
    contact_id: UUID,
    *,
    limit: int = 50,
) -> list[ContactActivity]:
    stmt = (
        select(ContactActivity)
        .where(ContactActivity.contact_id == contact_id)
        .order_by(desc(ContactActivity.occurred_at))
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars())


async def add_activity(
    db: AsyncSession,
    *,
    contact_id: UUID,
    kind: str,
    title: str | None,
    body: str | None,
    direction: str | None,
    channel: str | None,
    duration_seconds: int | None,
    metadata: dict[str, Any] | None,
    occurred_at: datetime | None,
    user_id: UUID | None,
) -> ContactActivity:
    contact = await db.get(Contact, contact_id)
    if contact is None:
        raise ValueError("Contact not found")
    rec = ContactActivity(
        contact_id=contact_id,
        kind=kind,
        title=title,
        body=body,
        direction=direction,
        channel=channel,
        duration_seconds=duration_seconds,
        metadata_=metadata,
        occurred_at=occurred_at or datetime.now(UTC),
        created_by=user_id,
    )
    db.add(rec)
    await db.flush()
    # Refresh score on each activity insert
    activities = await list_activities(db, contact_id, limit=30)
    score, reason = compute_score(contact, activities)
    contact.ai_score = score
    contact.ai_score_reason = reason
    contact.ai_score_updated_at = datetime.now(UTC)
    await db.flush()
    return rec


# ─────────── AI-flavoured re-score ───────────


async def score_with_ai(
    db: AsyncSession, contact_id: UUID
) -> tuple[int, str] | None:
    """Optional AI rescoring: feeds activity summary to ai_service.

    Falls back to the deterministic score on any failure / no creds.
    """
    from app.services import ai_service  # avoid cycle

    contact = await db.get(Contact, contact_id)
    if contact is None:
        return None
    activities = await list_activities(db, contact_id, limit=30)
    base_score, base_reason = compute_score(contact, activities)
    contact.ai_score = base_score
    contact.ai_score_reason = base_reason
    contact.ai_score_updated_at = datetime.now(UTC)

    if not activities:
        await db.flush()
        return base_score, base_reason

    activity_summary = "\n".join(
        f"- {a.occurred_at.date().isoformat()} [{a.kind}/{a.channel or '-'}] "
        f"{(a.title or a.body or '')[:120]}"
        for a in activities[:10]
    )
    system = (
        "You are a senior CRM analyst. Rate this contact's likelihood to convert "
        "(0-100) and provide a 1-sentence reason in O'zbek lotin. Return JSON "
        'EXACTLY as: {"score": <int>, "reason": "<text>"}. No markdown.'
    )
    user = (
        f"Contact: {contact.full_name}\n"
        f"Status: {contact.status}\n"
        f"Industry: {contact.industry or '—'}\n"
        f"Tags: {', '.join(contact.tags or []) or '—'}\n\n"
        f"Recent activities:\n{activity_summary}"
    )
    try:
        resp = await ai_service.complete(db, system=system, user=user, max_tokens=200)
    except Exception:
        await db.flush()
        return base_score, base_reason

    parsed = _parse_ai_score(resp.text)
    if parsed is None:
        await db.flush()
        return base_score, base_reason

    score, reason = parsed
    contact.ai_score = score
    contact.ai_score_reason = reason
    contact.ai_score_updated_at = datetime.now(UTC)
    await db.flush()
    return score, reason


def _parse_ai_score(text: str) -> tuple[int, str] | None:
    if not text or "{" not in text:
        return None
    try:
        import json

        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
    except (ValueError, KeyError):
        return None
    score = data.get("score")
    reason = data.get("reason")
    if not isinstance(score, int | float) or not isinstance(reason, str):
        return None
    return max(0, min(100, int(score))), reason[:500]


# ─────────── Stats ───────────


async def stats(db: AsyncSession) -> dict[str, Any]:
    rows = list((await db.execute(select(Contact))).scalars())
    by_status: dict[str, int] = {}
    hot = 0
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        if r.ai_score >= 75:
            hot += 1
    last_week = datetime.now(UTC) - timedelta(days=7)
    new_last_week = sum(1 for r in rows if r.created_at >= last_week)
    return {
        "total": len(rows),
        "by_status": by_status,
        "hot_leads": hot,
        "new_last_week": new_last_week,
    }


__all__ = [
    "ENGAGEMENT_KIND_WEIGHT",
    "add_activity",
    "compute_score",
    "create_contact",
    "delete_contact",
    "get_contact",
    "list_activities",
    "list_contacts",
    "score_with_ai",
    "stats",
    "update_contact",
]
