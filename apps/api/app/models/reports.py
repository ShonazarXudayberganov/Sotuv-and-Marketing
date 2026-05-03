"""Reports/BI: saved cross-module dashboard definitions per tenant."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class SavedReport(Base, UUIDPKMixin, TimestampMixin):
    """A user-saved cross-module report definition.

    ``definition`` is a JSON document describing widgets:
    {
      "widgets": [
        {"type": "kpi", "source": "smm.engagement_rate"},
        {"type": "funnel", "source": "crm.deals"},
        {"type": "timeseries", "source": "ads.spend", "days": 30}
      ],
      "filters": {"brand_id": "...", "date_from": "...", "date_to": "..."}
    }
    """

    __tablename__ = "saved_reports"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    definition: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    created_by: Mapped[UUID] = mapped_column(nullable=False)


__all__ = ["SavedReport"]
