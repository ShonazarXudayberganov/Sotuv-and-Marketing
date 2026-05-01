"""CRM-scoped models — Contact + ContactActivity.

Both live in each tenant's PostgreSQL schema. Sprint 2.1 covers contacts
and activity feed; deals/pipeline ship in Sprint 2.2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Contact(Base, UUIDPKMixin, TimestampMixin):
    """A CRM contact — person or company representative."""

    __tablename__ = "contacts"

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    email: Mapped[str | None] = mapped_column(String(160), index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(80))
    instagram_username: Mapped[str | None] = mapped_column(String(80))
    industry: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(50))  # inbox, website, manual, import
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="lead", index=True
    )  # lead, active, customer, lost, archived
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    assignee_id: Mapped[UUID | None] = mapped_column()
    ai_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    ai_score_reason: Mapped[str | None] = mapped_column(String(500))
    ai_score_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    custom_fields: Mapped[dict[str, object] | None] = mapped_column(JSON)
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)


class ContactActivity(Base, UUIDPKMixin, TimestampMixin):
    """Single timeline entry for a contact: call, message, note, task, email…"""

    __tablename__ = "contact_activities"

    contact_id: Mapped[UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    # call_in, call_out, message_in, message_out, email, note, task, meeting, status_change
    title: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str | None] = mapped_column(String(10))  # in, out, internal
    channel: Mapped[str | None] = mapped_column(String(30))  # phone, telegram, email, instagram…
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_by: Mapped[UUID | None] = mapped_column()


class Pipeline(Base, UUIDPKMixin, TimestampMixin):
    """A named sales pipeline (Asosiy sotuv, VIP, Servis xizmati…)."""

    __tablename__ = "pipelines"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column()


class PipelineStage(Base, UUIDPKMixin, TimestampMixin):
    """A stage inside a pipeline (Yangi → Bog'lanildi → Muzokara → …)."""

    __tablename__ = "pipeline_stages"

    pipeline_id: Mapped[UUID] = mapped_column(
        ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    default_probability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20))


class Deal(Base, UUIDPKMixin, TimestampMixin):
    """A sales opportunity tied to a contact and a pipeline stage."""

    __tablename__ = "deals"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL"), index=True
    )
    pipeline_id: Mapped[UUID] = mapped_column(
        ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage_id: Mapped[UUID] = mapped_column(
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # minor units
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)
    probability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open", index=True
    )  # open, won, lost
    is_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expected_close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    assignee_id: Mapped[UUID | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)


__all__ = ["Contact", "ContactActivity", "Deal", "Pipeline", "PipelineStage"]
