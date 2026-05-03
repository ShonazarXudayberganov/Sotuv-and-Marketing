"""Marketplace: incoming webhook endpoints + outbound delivery log.

Each tenant can register N inbound webhook endpoints with HMAC secrets,
plus subscribe to outbound delivery for events (contact.created,
deal.won, post.published, etc.).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class WebhookEndpoint(Base, UUIDPKMixin, TimestampMixin):
    """Inbound or outbound webhook endpoint.

    direction='in'  → external system POSTs to /api/v1/webhooks/in/{id}
    direction='out' → we POST to ``url`` whenever a subscribed event fires
    """

    __tablename__ = "webhook_endpoints"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # in, out
    url: Mapped[str | None] = mapped_column(String(500))
    secret: Mapped[str] = mapped_column(String(120), nullable=False)
    events: Mapped[list[str] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[int | None] = mapped_column(Integer)
    last_error: Mapped[str | None] = mapped_column(String(500))
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)


class WebhookDelivery(Base, UUIDPKMixin, TimestampMixin):
    """Per-attempt delivery record (audit + retry tracking)."""

    __tablename__ = "webhook_deliveries"

    endpoint_id: Mapped[UUID] = mapped_column(
        ForeignKey("webhook_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    event: Mapped[str | None] = mapped_column(String(80))
    status_code: Mapped[int | None] = mapped_column(Integer)
    request_body: Mapped[str | None] = mapped_column(Text)
    response_body: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    succeeded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error: Mapped[str | None] = mapped_column(String(500))


__all__ = ["WebhookDelivery", "WebhookEndpoint"]
