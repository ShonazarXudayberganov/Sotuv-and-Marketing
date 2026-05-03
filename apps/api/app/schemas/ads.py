from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

NETWORKS = ("meta", "google")
OBJECTIVES = ("awareness", "traffic", "leads", "conversions", "sales")


class AdAccountOut(BaseModel):
    id: UUID
    network: str
    external_id: str
    name: str
    currency: str
    status: str
    brand_id: UUID | None
    is_default: bool
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignOut(BaseModel):
    id: UUID
    account_id: UUID
    network: str
    external_id: str | None
    name: str
    objective: str
    status: str
    daily_budget: int
    lifetime_budget: int | None
    currency: str
    starts_at: datetime | None
    ends_at: datetime | None
    audience: dict[str, Any] | None
    creative: dict[str, Any] | None
    notes: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MetricsOut(BaseModel):
    impressions: int
    clicks: int
    conversions: int
    spend: int
    revenue: int
    ctr: int  # basis points
    cpc: int
    cpa: int
    sampled_at: datetime | None


class CampaignWithMetrics(CampaignOut):
    metrics: MetricsOut | None


class CampaignDraftRequest(BaseModel):
    account_id: UUID
    name: str = Field(min_length=2, max_length=200)
    objective: str = Field(default="traffic")
    daily_budget: int = Field(default=0, ge=0)
    currency: str = Field(default="UZS", min_length=3, max_length=3)
    audience: dict[str, Any] | None = None
    creative: dict[str, Any] | None = None
    notes: str | None = None


class CampaignPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    objective: str | None = None
    status: str | None = None
    daily_budget: int | None = Field(default=None, ge=0)
    lifetime_budget: int | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    audience: dict[str, Any] | None = None
    creative: dict[str, Any] | None = None
    notes: str | None = None


class AdsOverview(BaseModel):
    campaigns: int
    impressions: int
    clicks: int
    conversions: int
    spend: int
    revenue: int
    ctr: float
    cpc: int
    cpa: int
    roas: float
    by_network: dict[str, dict[str, int]]


class AdsTimePoint(BaseModel):
    date: str
    impressions: int
    clicks: int
    conversions: int
    spend: int
    revenue: int


class AdsInsightsOut(BaseModel):
    summary: str
    recommendations: list[str]
    snapshot: AdsOverview


class SyncResult(BaseModel):
    inserted: int
