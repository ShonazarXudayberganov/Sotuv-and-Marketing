"""Integration tests for the auth flow: register → verify-phone → login → refresh."""

import re

import pytest
from httpx import AsyncClient

from app.services.sms import MockSMSProvider

pytestmark = pytest.mark.asyncio


def _extract_code_from_sms(phone: str) -> str:
    for sent_phone, message in MockSMSProvider.sent:
        if sent_phone == phone:
            match = re.search(r"\b(\d{4,8})\b", message)
            if match:
                return match.group(1)
    raise AssertionError(f"No SMS sent to {phone}")


async def test_register_starts_verification(client: AsyncClient, sample_register_payload: dict):
    resp = await client.post("/api/v1/auth/register", json=sample_register_payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "verification_id" in body
    assert body["phone_masked"].startswith("+998")
    assert "***" in body["phone_masked"]
    assert len(MockSMSProvider.sent) == 1


async def test_register_rejects_weak_password(client: AsyncClient, sample_register_payload: dict):
    sample_register_payload["password"] = "weak"
    resp = await client.post("/api/v1/auth/register", json=sample_register_payload)
    assert resp.status_code == 422


async def test_register_rejects_missing_terms(client: AsyncClient, sample_register_payload: dict):
    sample_register_payload["accept_terms"] = False
    resp = await client.post("/api/v1/auth/register", json=sample_register_payload)
    assert resp.status_code == 422


async def test_register_duplicate_email_rejected(
    client: AsyncClient, sample_register_payload: dict
):
    # First registration completes via phone verification
    r1 = await client.post("/api/v1/auth/register", json=sample_register_payload)
    code = _extract_code_from_sms(sample_register_payload["phone"])
    await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": r1.json()["verification_id"], "code": code},
    )

    # Second registration with same email but different phone should be rejected
    second = {**sample_register_payload, "phone": "+998909999999"}
    resp = await client.post("/api/v1/auth/register", json=second)
    assert resp.status_code == 409


async def test_verify_phone_creates_tenant_and_returns_tokens(
    client: AsyncClient, sample_register_payload: dict
):
    reg = await client.post("/api/v1/auth/register", json=sample_register_payload)
    code = _extract_code_from_sms(sample_register_payload["phone"])

    resp = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == sample_register_payload["email"]
    assert body["user"]["role"] == "owner"
    assert body["tenant"]["name"] == sample_register_payload["company_name"]
    assert body["tenant"]["schema_name"].startswith("tenant_")


async def test_verify_phone_rejects_wrong_code(client: AsyncClient, sample_register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=sample_register_payload)
    resp = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": "000000"},
    )
    assert resp.status_code == 400


async def test_login_returns_tokens(client: AsyncClient, sample_register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=sample_register_payload)
    code = _extract_code_from_sms(sample_register_payload["phone"])
    await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email_or_phone": sample_register_payload["email"],
            "password": sample_register_payload["password"],
            "remember_me": False,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_with_phone_works(client: AsyncClient, sample_register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=sample_register_payload)
    code = _extract_code_from_sms(sample_register_payload["phone"])
    await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email_or_phone": sample_register_payload["phone"],
            "password": sample_register_payload["password"],
        },
    )
    assert resp.status_code == 200


async def test_login_rejects_wrong_password(client: AsyncClient, sample_register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=sample_register_payload)
    code = _extract_code_from_sms(sample_register_payload["phone"])
    await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email_or_phone": sample_register_payload["email"],
            "password": "WrongPass99",
        },
    )
    assert resp.status_code == 401


async def test_refresh_returns_new_access_token(client: AsyncClient, sample_register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=sample_register_payload)
    code = _extract_code_from_sms(sample_register_payload["phone"])
    verify = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    refresh_token = verify.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_refresh_rejects_access_token(client: AsyncClient, sample_register_payload: dict):
    reg = await client.post("/api/v1/auth/register", json=sample_register_payload)
    code = _extract_code_from_sms(sample_register_payload["phone"])
    verify = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    access = verify.json()["access_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401


async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
