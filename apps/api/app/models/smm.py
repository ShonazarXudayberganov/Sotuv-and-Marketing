"""SMM-scoped models — Brand + TenantIntegration (encrypted credentials).

Both live in each tenant's PostgreSQL schema.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Brand(Base, UUIDPKMixin, TimestampMixin):
    """A tenant can manage multiple brands (e.g. holding company)."""

    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(1000))
    industry: Mapped[str | None] = mapped_column(String(50))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str | None] = mapped_column(String(20))
    voice_tone: Mapped[str | None] = mapped_column(String(500))
    target_audience: Mapped[str | None] = mapped_column(Text)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)


class BrandMembership(Base, UUIDPKMixin, TimestampMixin):
    """Which users manage which brands. Users w/o membership see only the default."""

    __tablename__ = "brand_memberships"

    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), default="manager", nullable=False)


class TenantIntegration(Base, UUIDPKMixin, TimestampMixin):
    """Encrypted credentials for third-party providers, configured by the tenant.

    `credentials_encrypted` is a JSON string encrypted with Fernet (symmetric).
    Provider keys: anthropic, openai, telegram_bot, meta_app, google_oauth, eskiz_sms,
    sendgrid, instagram_business, facebook_page, youtube_channel.
    """

    __tablename__ = "tenant_integrations"

    provider: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    label: Mapped[str | None] = mapped_column(String(100))
    credentials_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(500))
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)
    created_by: Mapped[UUID] = mapped_column(nullable=False)


class BrandSocialAccount(Base, UUIDPKMixin, TimestampMixin):
    """A linked external account (channel/page/profile) on a social platform.

    Brand-scoped — each brand can link multiple Telegram channels, IG profiles, etc.
    The bot/app credentials live in ``tenant_integrations`` (one per tenant).
    """

    __tablename__ = "brand_social_accounts"

    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    external_handle: Mapped[str | None] = mapped_column(String(100))
    external_name: Mapped[str | None] = mapped_column(String(200))
    chat_type: Mapped[str | None] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(500))
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)
    created_by: Mapped[UUID] = mapped_column(nullable=False)


__all__ = ["Brand", "BrandMembership", "BrandSocialAccount", "TenantIntegration"]
