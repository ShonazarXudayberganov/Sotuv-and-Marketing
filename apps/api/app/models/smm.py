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


class ContentDraft(Base, UUIDPKMixin, TimestampMixin):
    """AI-generated content for a brand — preserved as a draft until scheduled.

    A draft remains editable; once scheduled or published it becomes a Post
    (Sprint 1.7).
    """

    __tablename__ = "content_drafts"

    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    user_goal: Mapped[str | None] = mapped_column(String(2000))
    language: Mapped[str] = mapped_column(String(10), default="uz", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(30))
    model: Mapped[str | None] = mapped_column(String(80))
    tokens_used: Mapped[int] = mapped_column(default=0, nullable=False)
    rag_chunk_ids: Mapped[list[str] | None] = mapped_column(JSON)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cache_key: Mapped[str | None] = mapped_column(String(80), index=True)
    created_by: Mapped[UUID] = mapped_column(nullable=False)


class Post(Base, UUIDPKMixin, TimestampMixin):
    """Scheduled / published social-media post.

    A Post fans out to one or more PostPublication rows — one per linked
    BrandSocialAccount target. status flows draft → scheduled → publishing
    → published / failed; the worker sweeps `scheduled_at <= now()` and
    transitions atomically to avoid double-publishes.
    """

    __tablename__ = "posts"

    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_drafts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list[str] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(1000))
    created_by: Mapped[UUID] = mapped_column(nullable=False)


class PostPublication(Base, UUIDPKMixin, TimestampMixin):
    """One attempt to publish a Post to a single linked social account."""

    __tablename__ = "post_publications"

    post_id: Mapped[UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    social_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("brand_social_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_post_id: Mapped[str | None] = mapped_column(String(120))
    last_error: Mapped[str | None] = mapped_column(String(1000))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


__all__ = [
    "Brand",
    "BrandMembership",
    "BrandSocialAccount",
    "ContentDraft",
    "Post",
    "PostPublication",
    "TenantIntegration",
]
