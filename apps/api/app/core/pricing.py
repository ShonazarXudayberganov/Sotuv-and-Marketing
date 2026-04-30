"""Static pricing constants — source of truth for billing.

All prices in soum (UZS). 1_000 = 1k so'm.
"""

from __future__ import annotations

from typing import Final, Literal

Module = Literal["crm", "smm", "ads", "inbox", "reports", "integrations"]
Tier = Literal["start", "pro", "business"]

MODULE_PRICES: Final[dict[str, dict[str, int]]] = {
    "crm": {"start": 290_000, "pro": 690_000, "business": 1_400_000},
    "smm": {"start": 390_000, "pro": 890_000, "business": 1_800_000},
    "ads": {"start": 290_000, "pro": 690_000, "business": 1_400_000},
    "inbox": {"start": 390_000, "pro": 890_000, "business": 1_800_000},
    "reports": {"start": 190_000, "pro": 490_000, "business": 990_000},
    "integrations": {"start": 190_000, "pro": 490_000, "business": 990_000},
}

# Per-tier monthly AI token caps
AI_TOKEN_CAPS: Final[dict[str, int]] = {
    "start": 50_000,
    "pro": 200_000,
    "business": 1_000_000,
}

# Bundle discounts (-15% / -25% on the sum of selected modules at a given tier)
PACKAGES: Final[dict[str, dict[str, object]]] = {
    "marketing": {
        "modules": ["smm", "ads", "inbox"],
        "discount_percent": 15,
        "label": "Marketing Pack",
    },
    "sales": {
        "modules": ["crm", "inbox", "reports"],
        "discount_percent": 15,
        "label": "Sales Pack",
    },
    "full": {
        "modules": ["crm", "smm", "ads", "inbox", "reports", "integrations"],
        "discount_percent": 25,
        "label": "Full Ecosystem",
    },
}

# Annual / semi-annual discount on top of base
CYCLE_DISCOUNTS: Final[dict[int, int]] = {1: 0, 6: 10, 12: 20}

TRIAL_DAYS: Final[int] = 7
GRACE_BANNER_DAYS: Final[int] = 7
GRACE_READONLY_DAYS: Final[int] = 30
GRACE_LOCK_DAYS: Final[int] = 90


def calc_subscription_price(
    modules: list[str],
    tier: str,
    package: str | None = None,
    billing_cycle_months: int = 1,
) -> tuple[int, int]:
    """Return ``(price_total, discount_percent)`` for the chosen modules+tier+cycle.

    If ``package`` is set we substitute its module list and apply the package
    discount; otherwise modules are charged individually at the chosen tier.
    """
    if package and package in PACKAGES:
        pkg = PACKAGES[package]
        pkg_modules = pkg["modules"]
        pkg_discount = pkg["discount_percent"]
        assert isinstance(pkg_modules, list)
        assert isinstance(pkg_discount, int)
        modules = list(pkg_modules)
        discount = pkg_discount
    else:
        discount = 0

    base = sum(MODULE_PRICES[m][tier] for m in modules if m in MODULE_PRICES)
    cycle_discount = CYCLE_DISCOUNTS.get(billing_cycle_months, 0)
    total_discount = min(50, discount + cycle_discount)
    monthly = base * (100 - total_discount) // 100
    return monthly * billing_cycle_months, total_discount


def ai_cap_for_tier(tier: str) -> int:
    return AI_TOKEN_CAPS.get(tier, 0)
