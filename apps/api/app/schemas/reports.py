from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CRMSnapshot(BaseModel):
    contacts_total: int
    hot_leads: int
    new_last_week: int
    by_status: dict[str, int]
    deals_open: int
    deals_won: int
    won_amount: int
    win_rate: float
    forecast_weighted: int
    forecast_open_amount: int


class SMMSnapshot(BaseModel):
    posts: int
    views: int
    likes: int
    comments: int
    engagement_rate: float
    by_platform: dict[str, dict[str, int]]


class AdsSnapshot(BaseModel):
    campaigns: int
    impressions: int
    clicks: int
    conversions: int
    spend: int
    revenue: int
    ctr: float
    roas: float
    by_network: dict[str, dict[str, int]]


class InboxSnapshot(BaseModel):
    conversations_total: int
    messages_in: int
    messages_out: int
    auto_replies: int
    response_rate: float


class ReportsOverview(BaseModel):
    period_days: int
    crm: CRMSnapshot
    smm: SMMSnapshot
    ads: AdsSnapshot
    inbox: InboxSnapshot


class FunnelTotals(BaseModel):
    contacts: int
    deals: int
    closed_deals: int
    conversion_rate: float


class FunnelOut(BaseModel):
    contacts: dict[str, int]
    deals: dict[str, int]
    totals: FunnelTotals


class CohortRow(BaseModel):
    month: str
    size: int
    customers: int
    lost: int


class SavedReportOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    definition: dict[str, Any]
    is_pinned: bool
    is_default: bool
    department_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SavedReportCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    definition: dict[str, Any]
    is_pinned: bool = False
    department_id: UUID | None = None


class SavedReportPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    definition: dict[str, Any] | None = None
    is_pinned: bool | None = None
    department_id: UUID | None = None


class ReportsInsightsOut(BaseModel):
    summary: str
    recommendations: list[str]
    snapshot: ReportsOverview
    funnel: FunnelOut
