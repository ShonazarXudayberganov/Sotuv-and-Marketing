from datetime import UTC, datetime, timedelta

import pytest

from app.models.billing import Subscription
from app.services.billing_service import GraceState, evaluate_grace


def _sub(expires_at: datetime) -> Subscription:
    return Subscription(
        selected_modules=["crm"],
        tier="pro",
        package=None,
        billing_cycle_months=1,
        price_total=690_000,
        discount_percent=0,
        starts_at=expires_at - timedelta(days=30),
        expires_at=expires_at,
        is_trial=False,
        is_active=True,
    )


def test_no_subscription_is_locked():
    assert evaluate_grace(None) == GraceState.LOCKED


def test_active_when_not_yet_expired():
    sub = _sub(datetime.now(UTC) + timedelta(days=5))
    assert evaluate_grace(sub) == GraceState.ACTIVE


def test_banner_within_first_7_days_after_expiry():
    sub = _sub(datetime.now(UTC) - timedelta(days=3))
    assert evaluate_grace(sub) == GraceState.BANNER


def test_read_only_between_7_and_30_days():
    sub = _sub(datetime.now(UTC) - timedelta(days=20))
    assert evaluate_grace(sub) == GraceState.READ_ONLY


@pytest.mark.parametrize("days_past", [31, 60, 90, 120])
def test_locked_after_30_days(days_past: int):
    sub = _sub(datetime.now(UTC) - timedelta(days=days_past))
    assert evaluate_grace(sub) == GraceState.LOCKED
