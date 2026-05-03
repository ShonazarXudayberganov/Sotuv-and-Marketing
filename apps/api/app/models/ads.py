"""Ads: per-tenant ad accounts, campaigns, and metric snapshots.

Sprint 3.1 covers Meta Ads + Google Ads (read + draft create). Real
campaign editing/launching is gated behind explicit user approval and
ships in Sprint 3.2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class AdAccount(Base, UUIDPKMixin, TimestampMixin):
    """Tenant's ad account on a network (Meta Ads, Google Ads, …)."""

    __tablename__ = "ad_accounts"

    network: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # meta, google
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    brand_id: Mapped[UUID | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Campaign(Base, UUIDPKMixin, TimestampMixin):
    """An advertising campaign synced from the network or drafted in NEXUS."""

    __tablename__ = "campaigns"

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    network: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(
        String(40), nullable=False, default="traffic"
    )  # awareness, traffic, leads, conversions, sales
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )  # draft, paused, active, archived
    daily_budget: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    lifetime_budget: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    audience: Mapped[dict[str, object] | None] = mapped_column(JSON)
    creative: Mapped[dict[str, object] | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(nullable=False)


class AdMetricSnapshot(Base, UUIDPKMixin, TimestampMixin):
    """Daily-ish metric snapshot for a campaign (impressions, clicks, spend, CPC, CTR…)."""

    __tablename__ = "ad_metric_snapshots"

    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    network: Mapped[str] = mapped_column(String(20), nullable=False)
    sampled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spend: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    revenue: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    ctr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # ‱ basis points
    cpc: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cpa: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)


__all__ = ["AdAccount", "AdMetricSnapshot", "Campaign"]
