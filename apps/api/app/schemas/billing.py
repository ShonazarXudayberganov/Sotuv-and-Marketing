from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ModuleKey = Literal["crm", "smm", "ads", "inbox", "reports", "integrations"]
TierKey = Literal["start", "pro", "business"]
PackageKey = Literal["marketing", "sales", "full", "enterprise"]
CycleMonths = Literal[1, 6, 12]


class SubscriptionOut(BaseModel):
    id: UUID
    selected_modules: list[str]
    tier: str
    package: str | None
    billing_cycle_months: int
    price_total: int
    discount_percent: int
    starts_at: datetime
    expires_at: datetime
    is_trial: bool
    is_active: bool
    cancelled_at: datetime | None

    model_config = {"from_attributes": True}


class SubscriptionChangeRequest(BaseModel):
    modules: list[ModuleKey] = Field(min_length=1)
    tier: TierKey
    package: PackageKey | None = None
    billing_cycle_months: CycleMonths = 1


class InvoiceOut(BaseModel):
    id: UUID
    subscription_id: UUID
    invoice_number: str
    amount: int
    status: str
    payment_method: str
    paid_at: datetime | None
    due_at: datetime
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceQuoteRequest(BaseModel):
    modules: list[ModuleKey] = Field(min_length=1)
    tier: TierKey
    package: PackageKey | None = None
    billing_cycle_months: CycleMonths = 1


class PriceQuoteResponse(BaseModel):
    price_total: int
    discount_percent: int
    ai_token_cap_monthly: int


class BillingStatusResponse(BaseModel):
    subscription: SubscriptionOut | None
    grace_state: str  # active | banner | read_only | locked
    days_until_expiry: int | None
    days_past_expiry: int | None


class CatalogModule(BaseModel):
    key: str
    label: str
    prices: dict[str, int]


class CatalogResponse(BaseModel):
    modules: list[CatalogModule]
    packages: dict[str, dict[str, object]]
    cycle_discounts: dict[int, int]
    ai_token_caps: dict[str, int]
