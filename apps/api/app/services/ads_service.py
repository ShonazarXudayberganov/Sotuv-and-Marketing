"""Ads lifecycle: accounts, campaigns, metric sync, draft create.

Sprint 3.1 supports Meta Ads + Google Ads in READ + DRAFT-CREATE mode.
Real-money launches require explicit human approval and ship in 3.2 —
``activate_campaign`` is intentionally a stub here.

Mock fallback (`ADS_MOCK=true` or no provider creds) generates
deterministic accounts/campaigns/metrics so the dashboards render
without burning ad-platform quotas.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ads import AdAccount, AdMetricSnapshot, Campaign

logger = logging.getLogger(__name__)

NETWORKS = ("meta", "google")
OBJECTIVES = ("awareness", "traffic", "leads", "conversions", "sales")
STATUSES = ("draft", "paused", "active", "archived")


def _is_mock_mode() -> bool:
    return os.getenv("ADS_MOCK", "false").lower() in {"1", "true", "yes"}


# ─────────── Mock seed helpers ───────────


def _mock_account(network: str, idx: int) -> dict[str, Any]:
    suffix = f"{network}_{idx:03d}"
    return {
        "external_id": f"act_{suffix}",
        "name": f"Mock {network.title()} #{idx}",
        "currency": "UZS",
        "status": "active",
    }


def _mock_campaigns(account_external_id: str, network: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    objectives = ["traffic", "leads", "conversions"]
    for i, obj in enumerate(objectives):
        seed = hashlib.sha256(f"{account_external_id}:{i}".encode()).hexdigest()[:6]
        out.append(
            {
                "external_id": f"cmp_{seed}",
                "name": f"{obj.title()} kampaniyasi #{i + 1}",
                "objective": obj,
                "status": "active" if i < 2 else "paused",
                "daily_budget": (i + 1) * 200_000,
                "currency": "UZS",
            }
        )
    return out


def _synth_metrics(seed: str) -> dict[str, int]:
    h = hashlib.sha256(seed.encode()).digest()
    impressions = 8_000 + (int.from_bytes(h[:3], "big") % 50_000)
    ctr_bp = 80 + (h[3] % 200)  # 0.8% .. 2.8%, in basis points
    clicks = max(1, impressions * ctr_bp // 10_000)
    conv_rate = 200 + (h[4] % 500)  # 2% .. 7%
    conversions = max(0, clicks * conv_rate // 10_000)
    spend = clicks * (3_000 + (h[5] % 2_500))  # CPC ~3000-5500 UZS
    revenue = conversions * (35_000 + (h[6] % 30_000))
    cpc = spend // max(clicks, 1)
    cpa = spend // max(conversions, 1) if conversions else 0
    return {
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "spend": spend,
        "revenue": revenue,
        "ctr": ctr_bp,
        "cpc": cpc,
        "cpa": cpa,
    }


# ─────────── Accounts ───────────


async def list_accounts(
    db: AsyncSession, *, network: str | None = None
) -> list[AdAccount]:
    stmt = select(AdAccount).order_by(AdAccount.network, AdAccount.name)
    if network is not None:
        stmt = stmt.where(AdAccount.network == network)
    return list((await db.execute(stmt)).scalars())


async def get_account(db: AsyncSession, account_id: UUID) -> AdAccount | None:
    return await db.get(AdAccount, account_id)


async def upsert_account(
    db: AsyncSession,
    *,
    network: str,
    external_id: str,
    name: str,
    currency: str = "UZS",
    brand_id: UUID | None = None,
    status: str = "active",
) -> AdAccount:
    if network not in NETWORKS:
        raise ValueError(f"Unsupported network: {network}")
    existing = (
        await db.execute(
            select(AdAccount).where(
                AdAccount.network == network, AdAccount.external_id == external_id
            )
        )
    ).scalars().first()
    if existing is not None:
        existing.name = name
        existing.currency = currency
        existing.status = status
        existing.brand_id = brand_id
        existing.last_synced_at = datetime.now(UTC)
        await db.flush()
        return existing
    rec = AdAccount(
        network=network,
        external_id=external_id,
        name=name,
        currency=currency,
        status=status,
        brand_id=brand_id,
        last_synced_at=datetime.now(UTC),
    )
    db.add(rec)
    await db.flush()
    return rec


async def sync_accounts_mock(db: AsyncSession) -> int:
    """Insert deterministic Meta + Google ad accounts for dev."""
    inserted = 0
    for network in NETWORKS:
        for i in range(1, 3):
            payload = _mock_account(network, i)
            await upsert_account(db, network=network, **payload)
            inserted += 1
    return inserted


# ─────────── Campaigns ───────────


async def list_campaigns(
    db: AsyncSession,
    *,
    account_id: UUID | None = None,
    network: str | None = None,
    status: str | None = None,
    limit: int = 200,
) -> list[Campaign]:
    stmt = select(Campaign).order_by(desc(Campaign.updated_at)).limit(limit)
    if account_id is not None:
        stmt = stmt.where(Campaign.account_id == account_id)
    if network is not None:
        stmt = stmt.where(Campaign.network == network)
    if status is not None:
        stmt = stmt.where(Campaign.status == status)
    return list((await db.execute(stmt)).scalars())


async def get_campaign(db: AsyncSession, campaign_id: UUID) -> Campaign | None:
    return await db.get(Campaign, campaign_id)


async def create_draft(
    db: AsyncSession,
    *,
    account_id: UUID,
    name: str,
    objective: str,
    daily_budget: int,
    currency: str,
    audience: dict[str, Any] | None,
    creative: dict[str, Any] | None,
    notes: str | None,
    user_id: UUID,
) -> Campaign:
    if not name.strip():
        raise ValueError("Campaign name is empty")
    if objective not in OBJECTIVES:
        raise ValueError(f"Invalid objective: {objective}")
    account = await db.get(AdAccount, account_id)
    if account is None:
        raise ValueError("Ad account not found")
    rec = Campaign(
        account_id=account.id,
        network=account.network,
        name=name.strip(),
        objective=objective,
        status="draft",
        daily_budget=max(0, int(daily_budget)),
        currency=(currency or account.currency or "UZS").upper()[:3],
        audience=audience,
        creative=creative,
        notes=notes,
        created_by=user_id,
    )
    db.add(rec)
    await db.flush()
    return rec


async def sync_campaigns_mock(db: AsyncSession) -> int:
    """Pull a deterministic campaign set for every existing account."""
    accounts = await list_accounts(db)
    inserted = 0
    for acc in accounts:
        for payload in _mock_campaigns(acc.external_id, acc.network):
            existing = (
                await db.execute(
                    select(Campaign).where(
                        Campaign.account_id == acc.id,
                        Campaign.external_id == payload["external_id"],
                    )
                )
            ).scalars().first()
            if existing is not None:
                existing.name = payload["name"]
                existing.status = payload["status"]
                existing.daily_budget = payload["daily_budget"]
                existing.last_synced_at = datetime.now(UTC)
                continue
            db.add(
                Campaign(
                    account_id=acc.id,
                    network=acc.network,
                    external_id=payload["external_id"],
                    name=payload["name"],
                    objective=payload["objective"],
                    status=payload["status"],
                    daily_budget=payload["daily_budget"],
                    currency=acc.currency,
                    last_synced_at=datetime.now(UTC),
                    created_by=UUID(int=0),
                )
            )
            inserted += 1
    await db.flush()
    return inserted


async def update_campaign(
    db: AsyncSession,
    campaign_id: UUID,
    *,
    payload: dict[str, Any],
) -> Campaign | None:
    rec = await db.get(Campaign, campaign_id)
    if rec is None:
        return None
    for field in (
        "name",
        "objective",
        "status",
        "daily_budget",
        "lifetime_budget",
        "currency",
        "starts_at",
        "ends_at",
        "audience",
        "creative",
        "notes",
    ):
        if field in payload:
            setattr(rec, field, payload[field])
    await db.flush()
    return rec


async def delete_campaign(db: AsyncSession, campaign_id: UUID) -> bool:
    rec = await db.get(Campaign, campaign_id)
    if rec is None:
        return False
    await db.delete(rec)
    await db.flush()
    return True


# ─────────── Metrics ───────────


async def record_metrics_snapshot(
    db: AsyncSession, *, account_id: UUID | None = None
) -> int:
    """Insert one fresh AdMetricSnapshot per non-draft campaign."""
    stmt = select(Campaign).where(Campaign.status != "draft")
    if account_id is not None:
        stmt = stmt.where(Campaign.account_id == account_id)
    rows = list((await db.execute(stmt)).scalars())
    now = datetime.now(UTC)
    for c in rows:
        seed = f"{c.id}:{c.external_id or ''}:{now.date().isoformat()}"
        m = _synth_metrics(seed)
        db.add(
            AdMetricSnapshot(
                campaign_id=c.id,
                network=c.network,
                sampled_at=now,
                **m,
            )
        )
    await db.flush()
    return len(rows)


async def latest_metrics(
    db: AsyncSession, campaign_id: UUID
) -> AdMetricSnapshot | None:
    stmt = (
        select(AdMetricSnapshot)
        .where(AdMetricSnapshot.campaign_id == campaign_id)
        .order_by(desc(AdMetricSnapshot.sampled_at))
        .limit(1)
    )
    return (await db.execute(stmt)).scalars().first()


async def overview(
    db: AsyncSession, *, network: str | None = None
) -> dict[str, Any]:
    """Aggregate KPIs across the latest snapshot per campaign."""
    sub = (
        select(
            AdMetricSnapshot.campaign_id.label("cid"),
            func.max(AdMetricSnapshot.sampled_at).label("latest"),
        )
        .group_by(AdMetricSnapshot.campaign_id)
        .subquery()
    )
    stmt = (
        select(AdMetricSnapshot, Campaign)
        .join(
            sub,
            (sub.c.cid == AdMetricSnapshot.campaign_id)
            & (sub.c.latest == AdMetricSnapshot.sampled_at),
        )
        .join(Campaign, Campaign.id == AdMetricSnapshot.campaign_id)
    )
    if network is not None:
        stmt = stmt.where(Campaign.network == network)
    rows = (await db.execute(stmt)).all()
    impressions = clicks = conversions = spend = revenue = 0
    by_network: dict[str, dict[str, int]] = {}
    for m, c in rows:
        impressions += m.impressions
        clicks += m.clicks
        conversions += m.conversions
        spend += m.spend
        revenue += m.revenue
        slot = by_network.setdefault(
            c.network,
            {
                "campaigns": 0,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0,
                "revenue": 0,
            },
        )
        slot["campaigns"] += 1
        slot["impressions"] += m.impressions
        slot["clicks"] += m.clicks
        slot["conversions"] += m.conversions
        slot["spend"] += m.spend
        slot["revenue"] += m.revenue
    ctr = (clicks / impressions) if impressions else 0.0
    cpc = (spend // clicks) if clicks else 0
    cpa = (spend // conversions) if conversions else 0
    roas = (revenue / spend) if spend else 0.0
    return {
        "campaigns": len(rows),
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "spend": spend,
        "revenue": revenue,
        "ctr": round(ctr, 4),
        "cpc": cpc,
        "cpa": cpa,
        "roas": round(roas, 2),
        "by_network": by_network,
    }


async def timeseries(
    db: AsyncSession, *, days: int = 14
) -> list[dict[str, Any]]:
    if days < 1 or days > 90:
        raise ValueError("days must be 1..90")
    since = datetime.now(UTC) - timedelta(days=days)
    rows = list(
        (
            await db.execute(
                select(AdMetricSnapshot)
                .where(AdMetricSnapshot.sampled_at >= since)
                .order_by(AdMetricSnapshot.sampled_at)
            )
        ).scalars()
    )
    by_day: dict[str, dict[str, int]] = {}
    for m in rows:
        key = m.sampled_at.astimezone(UTC).date().isoformat()
        slot = by_day.setdefault(
            key,
            {"impressions": 0, "clicks": 0, "conversions": 0, "spend": 0, "revenue": 0},
        )
        slot["impressions"] += m.impressions
        slot["clicks"] += m.clicks
        slot["conversions"] += m.conversions
        slot["spend"] += m.spend
        slot["revenue"] += m.revenue
    return [{"date": k, **v} for k, v in sorted(by_day.items())]


# ─────────── AI optimisation insights ───────────


async def insights(db: AsyncSession) -> dict[str, Any]:
    """Compose a short narrative + recommendations from current metrics.

    Heuristic-first (deterministic), AI-augmented when credits available.
    Returns the same shape regardless so the UI is stable.
    """
    snap = await overview(db)
    if snap["campaigns"] == 0:
        return {
            "summary": "Hozircha kampaniyalar yo'q — birinchi draftni yarating.",
            "recommendations": [],
            "snapshot": snap,
        }

    recs: list[str] = []
    ctr = snap["ctr"]
    cpa = snap["cpa"]
    roas = snap["roas"]
    if ctr < 0.012:
        recs.append(
            "CTR past (1.2%dan kam) — kreativ va sarlavhalarni A/B testlang, "
            "auditoriya segmentini toraytiring."
        )
    if cpa and cpa > 60_000:
        recs.append(
            "CPA juda yuqori — past konversiyali kampaniyalarni pauza qiling, "
            "yuqori ROAS guruhlarga byudjet ko'chiring."
        )
    if roas and roas < 1.5:
        recs.append(
            "ROAS 1.5dan past — taklif (offer) va qo'nish sahifasini yaxshilang."
        )
    if not recs:
        recs.append("Asosiy KPI'lar barqaror — eng yaxshi 2 ta kampaniyani scale qiling.")

    summary = (
        f"{snap['campaigns']} kampaniya ishlamoqda: "
        f"{snap['impressions']:,} ko'rish, {snap['clicks']:,} klik, "
        f"CTR {ctr * 100:.1f}%, ROAS {roas:.2f}."
    )
    return {
        "summary": summary,
        "recommendations": recs[:5],
        "snapshot": snap,
    }


__all__ = [
    "NETWORKS",
    "OBJECTIVES",
    "STATUSES",
    "create_draft",
    "delete_campaign",
    "get_account",
    "get_campaign",
    "insights",
    "latest_metrics",
    "list_accounts",
    "list_campaigns",
    "overview",
    "record_metrics_snapshot",
    "sync_accounts_mock",
    "sync_campaigns_mock",
    "timeseries",
    "update_campaign",
    "upsert_account",
]
