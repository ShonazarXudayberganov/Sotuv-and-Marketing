from app.core.pricing import (
    AI_TOKEN_CAPS,
    MODULE_PRICES,
    ai_cap_for_tier,
    calc_subscription_price,
)


def test_single_module_pro_no_cycle_discount():
    price, discount = calc_subscription_price(["crm"], "pro")
    assert price == MODULE_PRICES["crm"]["pro"]
    assert discount == 0


def test_full_package_25_percent_discount():
    all_mods = ["crm", "smm", "ads", "inbox", "reports", "integrations"]
    price, discount = calc_subscription_price(all_mods, "pro", package="full")
    assert discount == 25
    base = sum(MODULE_PRICES[m]["pro"] for m in all_mods)
    assert price == base * 75 // 100


def test_annual_cycle_adds_20_percent_discount():
    price, discount = calc_subscription_price(["crm"], "pro", billing_cycle_months=12)
    assert discount == 20
    monthly = MODULE_PRICES["crm"]["pro"] * 80 // 100
    assert price == monthly * 12


def test_package_plus_annual_cycles_combined():
    price, discount = calc_subscription_price(
        ["smm", "ads", "inbox"], "pro", package="marketing", billing_cycle_months=12
    )
    # Marketing 15% + annual 20% = 35% (cap at 50)
    assert discount == 35


def test_ai_cap_per_tier():
    assert ai_cap_for_tier("start") == AI_TOKEN_CAPS["start"]
    assert ai_cap_for_tier("pro") == AI_TOKEN_CAPS["pro"]
    assert ai_cap_for_tier("business") == AI_TOKEN_CAPS["business"]
    assert ai_cap_for_tier("nonexistent") == 0
