"""Reports/BI: cross-module unified analytics + saved dashboards.

Pulls KPIs from CRM, SMM, Ads, and Inbox into one dashboard. Funnel,
cohorts, AI narrative — all backed by services we already have.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ads import AdMetricSnapshot, Campaign
from app.models.crm import Contact, Deal
from app.models.inbox import Conversation, Message
from app.models.reports import SavedReport
from app.models.smm import Post, PostMetrics, PostPublication
from app.services import ads_service, analytics_service, contact_service, deal_service

logger = logging.getLogger(__name__)


# ─────────── Cross-module overview ───────────


async def overview(db: AsyncSession, *, days: int = 30) -> dict[str, Any]:
    """Single dashboard payload pulling from CRM + SMM + Ads + Inbox."""
    if days < 1 or days > 365:
        raise ValueError("days must be 1..365")
    since = datetime.now(UTC) - timedelta(days=days)

    # CRM
    crm_stats = await contact_service.stats(db)
    deal_stats = await deal_service.stats(db)
    forecast = await deal_service.forecast(db)

    # SMM
    smm_overview = await analytics_service.overview(db)

    # Ads
    ads_overview = await ads_service.overview(db)

    # Inbox
    convs = list((await db.execute(select(Conversation))).scalars())
    msgs_in_window = list(
        (await db.execute(select(Message).where(Message.occurred_at >= since))).scalars()
    )
    inbound = sum(1 for m in msgs_in_window if m.direction == "in")
    outbound = sum(1 for m in msgs_in_window if m.direction == "out")
    auto_replies = sum(1 for m in msgs_in_window if m.is_auto_reply)
    response_rate = (outbound / inbound) if inbound else 0.0

    return {
        "period_days": days,
        "crm": {
            "contacts_total": crm_stats["total"],
            "hot_leads": crm_stats["hot_leads"],
            "new_last_week": crm_stats["new_last_week"],
            "by_status": crm_stats["by_status"],
            "deals_open": deal_stats["by_status"].get("open", 0),
            "deals_won": deal_stats["by_status"].get("won", 0),
            "won_amount": deal_stats["won_amount"],
            "win_rate": deal_stats["win_rate"],
            "forecast_weighted": forecast["weighted_amount"],
            "forecast_open_amount": forecast["open_amount"],
        },
        "smm": {
            "posts": smm_overview["total_posts"],
            "views": smm_overview["total_views"],
            "likes": smm_overview["total_likes"],
            "comments": smm_overview["total_comments"],
            "engagement_rate": smm_overview["engagement_rate"],
            "by_platform": smm_overview.get("by_platform") or {},
        },
        "ads": {
            "campaigns": ads_overview["campaigns"],
            "impressions": ads_overview["impressions"],
            "clicks": ads_overview["clicks"],
            "conversions": ads_overview["conversions"],
            "spend": ads_overview["spend"],
            "revenue": ads_overview["revenue"],
            "ctr": ads_overview["ctr"],
            "roas": ads_overview["roas"],
            "by_network": ads_overview.get("by_network") or {},
        },
        "inbox": {
            "conversations_total": len(convs),
            "messages_in": inbound,
            "messages_out": outbound,
            "auto_replies": auto_replies,
            "response_rate": round(response_rate, 4),
        },
    }


# ─────────── Funnel ───────────


async def funnel(db: AsyncSession) -> dict[str, Any]:
    """Lead → contacted → negotiation → proposal → won/lost.

    Built from contacts (lead-stage) + deals' probability-driven stages.
    """
    contacts = list((await db.execute(select(Contact))).scalars())
    deals = list((await db.execute(select(Deal))).scalars())

    leads = sum(1 for c in contacts if c.status == "lead")
    active = sum(1 for c in contacts if c.status == "active")
    customers = sum(1 for c in contacts if c.status == "customer")

    deal_buckets: dict[str, int] = {
        "new": 0,
        "contacted": 0,
        "negotiation": 0,
        "proposal": 0,
        "agreed": 0,
        "won": 0,
        "lost": 0,
    }
    for d in deals:
        if d.status == "won":
            deal_buckets["won"] += 1
        elif d.status == "lost":
            deal_buckets["lost"] += 1
        else:
            # Bucket by probability ladder (rough proxy without joining stages)
            if d.probability >= 80:
                deal_buckets["agreed"] += 1
            elif d.probability >= 60:
                deal_buckets["proposal"] += 1
            elif d.probability >= 40:
                deal_buckets["negotiation"] += 1
            elif d.probability >= 25:
                deal_buckets["contacted"] += 1
            else:
                deal_buckets["new"] += 1

    won = deal_buckets["won"]
    closed = won + deal_buckets["lost"]
    conversion_rate = (won / closed) if closed else 0.0

    return {
        "contacts": {
            "lead": leads,
            "active": active,
            "customer": customers,
        },
        "deals": deal_buckets,
        "totals": {
            "contacts": len(contacts),
            "deals": len(deals),
            "closed_deals": closed,
            "conversion_rate": round(conversion_rate, 4),
        },
    }


# ─────────── Cohorts (monthly) ───────────


async def contact_cohorts(db: AsyncSession, *, months: int = 6) -> list[dict[str, Any]]:
    """Group contacts by created-at month and report cohort size + customers."""
    if months < 1 or months > 24:
        raise ValueError("months must be 1..24")
    since = datetime.now(UTC) - timedelta(days=months * 31)
    rows = list((await db.execute(select(Contact).where(Contact.created_at >= since))).scalars())
    by_month: dict[str, dict[str, int]] = {}
    for c in rows:
        key = c.created_at.astimezone(UTC).strftime("%Y-%m")
        slot = by_month.setdefault(key, {"size": 0, "customers": 0, "lost": 0})
        slot["size"] += 1
        if c.status == "customer":
            slot["customers"] += 1
        elif c.status == "lost":
            slot["lost"] += 1
    return [{"month": k, **v} for k, v in sorted(by_month.items())]


# ─────────── Saved reports CRUD ───────────


async def list_saved(db: AsyncSession) -> list[SavedReport]:
    stmt = select(SavedReport).order_by(desc(SavedReport.is_pinned), desc(SavedReport.updated_at))
    return list((await db.execute(stmt)).scalars())


async def get_saved(db: AsyncSession, report_id: UUID) -> SavedReport | None:
    return await db.get(SavedReport, report_id)


async def create_saved(
    db: AsyncSession,
    *,
    name: str,
    description: str | None,
    definition: dict[str, Any],
    is_pinned: bool,
    department_id: UUID | None,
    user_id: UUID,
) -> SavedReport:
    if not name.strip():
        raise ValueError("Report name is empty")
    rec = SavedReport(
        name=name.strip(),
        description=description,
        definition=definition,
        is_pinned=is_pinned,
        department_id=department_id,
        created_by=user_id,
    )
    db.add(rec)
    await db.flush()
    return rec


async def update_saved(
    db: AsyncSession,
    report_id: UUID,
    *,
    payload: dict[str, Any],
) -> SavedReport | None:
    rec = await db.get(SavedReport, report_id)
    if rec is None:
        return None
    for field in ("name", "description", "definition", "is_pinned", "department_id"):
        if field in payload:
            setattr(rec, field, payload[field])
    await db.flush()
    return rec


async def delete_saved(db: AsyncSession, report_id: UUID) -> bool:
    rec = await db.get(SavedReport, report_id)
    if rec is None:
        return False
    await db.delete(rec)
    await db.flush()
    return True


# ─────────── AI business insights ───────────


def _heuristic_insights(snap: dict[str, Any], fnl: dict[str, Any]) -> dict[str, Any]:
    recs: list[str] = []
    crm = snap["crm"]
    smm = snap["smm"]
    ads = snap["ads"]
    inbox = snap["inbox"]

    if crm["hot_leads"] > 0 and crm["deals_open"] < crm["hot_leads"]:
        recs.append(
            f"{crm['hot_leads']} ta issiq lead bor — har biri uchun bitim yarating va "
            "voronkaga kiriting."
        )
    if ads["roas"] and ads["roas"] < 1.5:
        recs.append(
            "Reklama ROAS 1.5dan past — past CTR'li kreativlarni pauza qiling, "
            "yuqori konversiyalilarga byudjet ko'chiring."
        )
    if smm["engagement_rate"] and smm["engagement_rate"] < 0.02:
        recs.append(
            "SMM engagement past — kontent rejani brand voice va RAG bilim bazasiga "
            "tortib qayta ko'rib chiqing."
        )
    if inbox["messages_in"] and inbox["response_rate"] < 0.5:
        recs.append(
            "Inbox response rate 50%dan past — auto-reply yoqilganligini va "
            "operator vaqtini tekshiring."
        )
    if fnl["totals"]["conversion_rate"] and fnl["totals"]["conversion_rate"] < 0.2:
        recs.append(
            "Bitim yopilish ulushi 20%dan past — taklif (offer) va qo'nish "
            "sahifasini yaxshilash kerak."
        )
    if not recs:
        recs.append(
            "Asosiy ko'rsatkichlar barqaror — eng yaxshi kanallarga ko'proq "
            "byudjet ajrating va A/B testni davom ettiring."
        )

    summary = (
        f"Oxirgi {snap['period_days']} kun: {crm['contacts_total']} mijoz, "
        f"{crm['deals_open']} ochiq bitim ({crm['forecast_weighted']:,} "
        f"forecast). SMM engagement {smm['engagement_rate'] * 100:.1f}%, "
        f"reklama ROAS {ads['roas']:.2f}x."
    )
    return {"summary": summary, "recommendations": recs[:5]}


async def insights(db: AsyncSession, *, days: int = 30) -> dict[str, Any]:
    snap = await overview(db, days=days)
    fnl = await funnel(db)
    base = _heuristic_insights(snap, fnl)

    if (
        snap["crm"]["contacts_total"] == 0
        and snap["smm"]["posts"] == 0
        and snap["ads"]["campaigns"] == 0
    ):
        return {
            "summary": "Hozircha ma'lumot kam — birinchi mijozlarni qo'shing, "
            "post yarating yoki reklama drafti tashlang.",
            "recommendations": [],
            "snapshot": snap,
            "funnel": fnl,
        }

    # AI augmentation (best-effort — heuristic stays as the source of truth)
    try:
        from app.services import ai_service

        system = (
            "You are a senior business analyst. Read the JSON snapshot and "
            "produce a 2-sentence executive summary in O'zbek lotin plus 3 "
            "concrete next-actions. Return ONLY: "
            '{"summary":"…","recommendations":["…","…","…"]}'
        )
        user = json.dumps({"snapshot": snap, "funnel": fnl}, ensure_ascii=False)
        resp = await ai_service.complete(db, system=system, user=user, max_tokens=400)
        parsed = _parse_ai(resp.text)
        if parsed:
            base = parsed
    except Exception as exc:
        logger.warning("Reports AI insights call failed (%s) — using heuristic", exc)

    return {**base, "snapshot": snap, "funnel": fnl}


def _parse_ai(text: str) -> dict[str, Any] | None:
    if not text or "{" not in text:
        return None
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
    except (ValueError, KeyError):
        return None
    summary = data.get("summary")
    recs = data.get("recommendations") or []
    if not isinstance(summary, str) or not isinstance(recs, list):
        return None
    return {"summary": summary, "recommendations": [str(r) for r in recs[:5] if r]}


# ─────────── Export ───────────


async def export_csv(db: AsyncSession, *, kind: str) -> str:
    """Return a CSV string for the given report kind."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    if kind == "contacts":
        contacts = list((await db.execute(select(Contact))).scalars())
        writer.writerow(["id", "full_name", "phone", "email", "status", "ai_score", "created_at"])
        for c in contacts:
            writer.writerow(
                [
                    c.id,
                    c.full_name,
                    c.phone or "",
                    c.email or "",
                    c.status,
                    c.ai_score,
                    c.created_at.isoformat(),
                ]
            )
    elif kind == "deals":
        deals = list((await db.execute(select(Deal))).scalars())
        writer.writerow(
            ["id", "title", "amount", "currency", "status", "probability", "created_at"]
        )
        for d in deals:
            writer.writerow(
                [
                    d.id,
                    d.title,
                    d.amount,
                    d.currency,
                    d.status,
                    d.probability,
                    d.created_at.isoformat(),
                ]
            )
    elif kind == "campaigns":
        campaigns = list((await db.execute(select(Campaign))).scalars())
        writer.writerow(
            ["id", "name", "network", "status", "objective", "daily_budget", "currency"]
        )
        for camp in campaigns:
            writer.writerow(
                [
                    camp.id,
                    camp.name,
                    camp.network,
                    camp.status,
                    camp.objective,
                    camp.daily_budget,
                    camp.currency,
                ]
            )
    elif kind == "ad_metrics":
        metrics = list((await db.execute(select(AdMetricSnapshot))).scalars())
        writer.writerow(
            [
                "campaign_id",
                "network",
                "sampled_at",
                "impressions",
                "clicks",
                "spend",
                "revenue",
            ]
        )
        for m in metrics:
            writer.writerow(
                [
                    m.campaign_id,
                    m.network,
                    m.sampled_at.isoformat(),
                    m.impressions,
                    m.clicks,
                    m.spend,
                    m.revenue,
                ]
            )
    elif kind == "posts":
        posts = list((await db.execute(select(Post))).scalars())
        writer.writerow(["id", "title", "status", "scheduled_at", "published_at"])
        for p in posts:
            writer.writerow(
                [
                    p.id,
                    p.title or "",
                    p.status,
                    p.scheduled_at.isoformat() if p.scheduled_at else "",
                    p.published_at.isoformat() if p.published_at else "",
                ]
            )
    else:
        raise ValueError(f"Unknown export kind: {kind}")
    return buf.getvalue()


# Touch unused imports so tools see them as used (PostMetrics + PostPublication
# are kept for future widgets that join on engagement metrics).
_ = (PostMetrics, PostPublication)


__all__ = [
    "contact_cohorts",
    "create_saved",
    "delete_saved",
    "export_csv",
    "funnel",
    "get_saved",
    "insights",
    "list_saved",
    "overview",
    "update_saved",
]
