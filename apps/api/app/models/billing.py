"""Billing models.

Plans live in the public schema (shared catalog). Subscriptions and Invoices
live in each tenant's schema.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Plan(Base, UUIDPKMixin, TimestampMixin):
    """Catalog row, e.g. ('crm', 'pro', 690_000)."""

    __tablename__ = "plans"
    __table_args__ = {"schema": "public"}

    module: Mapped[str] = mapped_column(String(30), nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    price_monthly: Mapped[int] = mapped_column(Integer, nullable=False)  # in soum
    ai_token_cap_monthly: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Subscription(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    selected_modules: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="start")
    package: Mapped[str | None] = mapped_column(String(30))  # marketing, sales, full, enterprise
    billing_cycle_months: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_total: Mapped[int] = mapped_column(Integer, nullable=False)  # in soum after discounts
    discount_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Invoice(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "invoices"

    subscription_id: Mapped[UUID] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    invoice_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, paid, cancelled
    payment_method: Mapped[str] = mapped_column(String(20), default="bank_transfer")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_by_user_id: Mapped[UUID | None] = mapped_column()
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000))


class AiUsage(Base, UUIDPKMixin, TimestampMixin):
    """Per-month AI token consumption (one row per tenant per YYYY-MM)."""

    __tablename__ = "ai_usage"

    period: Mapped[str] = mapped_column(String(7), nullable=False, unique=True)  # YYYY-MM
    tokens_used: Mapped[int] = mapped_column(Numeric, default=0, nullable=False)
    tokens_cap: Mapped[int] = mapped_column(Numeric, default=0, nullable=False)


__all__ = ["AiUsage", "Invoice", "Plan", "Subscription"]
