"""Subscription + invoice operations + grace period state machine."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pricing import (
    GRACE_LOCK_DAYS,
    GRACE_READONLY_DAYS,
    TRIAL_DAYS,
    calc_subscription_price,
)
from app.models.billing import Invoice, Subscription


class GraceState(str, Enum):
    ACTIVE = "active"
    BANNER = "banner"  # within 7 days past expiry
    READ_ONLY = "read_only"  # 7-30 days past
    LOCKED = "locked"  # 30+ days past


def evaluate_grace(sub: Subscription | None, now: datetime | None = None) -> GraceState:
    if sub is None:
        return GraceState.LOCKED
    now = now or datetime.now(UTC)
    if now <= sub.expires_at:
        return GraceState.ACTIVE
    delta_days = (now - sub.expires_at).days
    if delta_days <= 7:
        return GraceState.BANNER
    if delta_days <= GRACE_READONLY_DAYS:
        return GraceState.READ_ONLY
    if delta_days <= GRACE_LOCK_DAYS:
        return GraceState.LOCKED
    return GraceState.LOCKED


async def current_subscription(db: AsyncSession) -> Subscription | None:
    rows = (
        await db.execute(
            select(Subscription)
            .where(Subscription.is_active.is_(True))
            .order_by(Subscription.starts_at.desc())
            .limit(1)
        )
    ).scalars()
    return rows.first()


async def start_trial(db: AsyncSession) -> Subscription:
    """7-day trial with the Pro tier and the Full package — gives full access."""
    now = datetime.now(UTC)
    expires = now + timedelta(days=TRIAL_DAYS)
    price, discount = calc_subscription_price(
        modules=["crm", "smm", "ads", "inbox", "reports", "integrations"],
        tier="pro",
        package="full",
        billing_cycle_months=1,
    )
    sub = Subscription(
        selected_modules=["crm", "smm", "ads", "inbox", "reports", "integrations"],
        tier="pro",
        package="full",
        billing_cycle_months=1,
        price_total=price,
        discount_percent=discount,
        starts_at=now,
        expires_at=expires,
        is_trial=True,
        is_active=True,
    )
    db.add(sub)
    await db.flush()
    return sub


async def change_subscription(
    db: AsyncSession,
    *,
    modules: list[str],
    tier: str,
    package: str | None,
    billing_cycle_months: int,
) -> tuple[Subscription, Invoice]:
    """Replace the current subscription with a new one, generating an invoice."""
    existing = await current_subscription(db)
    if existing is not None:
        existing.is_active = False
        existing.cancelled_at = datetime.now(UTC)

    price, discount = calc_subscription_price(modules, tier, package, billing_cycle_months)
    now = datetime.now(UTC)
    expires = now + timedelta(days=30 * billing_cycle_months)
    sub = Subscription(
        selected_modules=modules,
        tier=tier,
        package=package,
        billing_cycle_months=billing_cycle_months,
        price_total=price,
        discount_percent=discount,
        starts_at=now,
        expires_at=expires,
        is_trial=False,
        is_active=True,
    )
    db.add(sub)
    await db.flush()

    invoice = Invoice(
        subscription_id=sub.id,
        invoice_number=_generate_invoice_number(),
        amount=price,
        status="pending",
        payment_method="bank_transfer",
        due_at=now + timedelta(days=7),
    )
    db.add(invoice)
    await db.flush()
    return sub, invoice


async def mark_invoice_paid(db: AsyncSession, invoice_id: UUID, paid_by_user_id: UUID) -> Invoice:
    inv = await db.get(Invoice, invoice_id)
    if inv is None:
        raise ValueError("Invoice not found")
    inv.status = "paid"
    inv.paid_at = datetime.now(UTC)
    inv.paid_by_user_id = paid_by_user_id
    await db.flush()
    return inv


def _generate_invoice_number() -> str:
    ts = datetime.now(UTC).strftime("%Y%m%d")
    suffix = secrets.token_hex(3).upper()
    return f"INV-{ts}-{suffix}"
