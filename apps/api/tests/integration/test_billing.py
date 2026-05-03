"""Integration tests for Sprint 5 billing endpoints."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sms import MockSMSProvider

pytestmark = pytest.mark.asyncio


def _code_for(phone: str) -> str:
    for sent_phone, message in MockSMSProvider.sent:
        if sent_phone == phone:
            match = re.search(r"\b(\d{4,8})\b", message)
            if match:
                return match.group(1)
    raise AssertionError(f"No SMS sent to {phone}")


async def _bootstrap(client: AsyncClient, payload: dict) -> dict:
    reg = await client.post("/api/v1/auth/register", json=payload)
    code = _code_for(payload["phone"])
    verify = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    return verify.json()


async def test_catalog_returns_modules_and_packages(client: AsyncClient):
    resp = await client.get("/api/v1/billing/catalog")
    assert resp.status_code == 200
    body = resp.json()
    assert {m["key"] for m in body["modules"]} == {
        "crm",
        "smm",
        "ads",
        "inbox",
        "reports",
        "integrations",
    }
    assert "full" in body["packages"]


async def test_quote_calculates_full_package_discount(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post(
        "/api/v1/billing/quote",
        headers=headers,
        json={
            "modules": ["crm", "smm", "ads", "inbox", "reports", "integrations"],
            "tier": "pro",
            "package": "full",
            "billing_cycle_months": 1,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["discount_percent"] == 25
    assert body["ai_token_cap_monthly"] == 200_000


async def test_billing_status_starts_with_no_subscription(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.get("/api/v1/billing/status", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["subscription"] is None
    assert body["grace_state"] == "locked"


async def test_start_trial_creates_active_subscription(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    trial = await client.post("/api/v1/billing/start-trial", headers=headers)
    assert trial.status_code == 201, trial.text
    assert trial.json()["is_trial"] is True
    assert trial.json()["package"] == "full"

    second = await client.post("/api/v1/billing/start-trial", headers=headers)
    assert second.status_code == 409


async def test_subscribe_creates_pending_invoice_and_email(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    resp = await client.post(
        "/api/v1/billing/subscribe",
        headers=headers,
        json={
            "modules": ["crm", "inbox"],
            "tier": "pro",
            "billing_cycle_months": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["amount"] > 0
    assert body["invoice_number"].startswith("INV-")


async def test_invoice_pdf_returns_binary_pdf(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    sub = await client.post(
        "/api/v1/billing/subscribe",
        headers=headers,
        json={"modules": ["crm"], "tier": "pro", "billing_cycle_months": 1},
    )
    invoice_id = sub.json()["id"]

    pdf = await client.get(f"/api/v1/billing/invoices/{invoice_id}/pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:4] == b"%PDF"


async def test_mark_paid_extends_subscription(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    sub_resp = await client.post(
        "/api/v1/billing/subscribe",
        headers=headers,
        json={"modules": ["crm"], "tier": "pro", "billing_cycle_months": 1},
    )
    invoice_id = sub_resp.json()["id"]

    paid = await client.post(f"/api/v1/billing/invoices/{invoice_id}/mark-paid", headers=headers)
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"
    assert paid.json()["paid_at"] is not None


async def test_invoice_listing(client: AsyncClient, sample_register_payload: dict):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}
    await client.post(
        "/api/v1/billing/subscribe",
        headers=headers,
        json={"modules": ["crm"], "tier": "start", "billing_cycle_months": 1},
    )
    listing = await client.get("/api/v1/billing/invoices", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_read_only_grace_blocks_writes_but_allows_reads(
    client: AsyncClient, sample_register_payload: dict, db_session: AsyncSession
):
    bundle = await _bootstrap(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    trial = await client.post("/api/v1/billing/start-trial", headers=headers)
    assert trial.status_code == 201, trial.text

    schema = bundle["tenant"]["schema_name"]
    await db_session.execute(text(f"SET search_path TO {schema}, public"))
    await db_session.execute(
        text("UPDATE subscriptions SET expires_at = :expired_at"),
        {"expired_at": datetime.now(UTC) - timedelta(days=20)},
    )
    await db_session.commit()

    read = await client.get("/api/v1/brands", headers=headers)
    assert read.status_code == 200

    write = await client.post("/api/v1/brands", headers=headers, json={"name": "Blocked"})
    assert write.status_code == 402
    assert "Faqat o'qish" in write.json()["detail"]
