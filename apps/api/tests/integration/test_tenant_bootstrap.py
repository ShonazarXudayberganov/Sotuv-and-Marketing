"""Integration tests for Sprint 3 — tenant bootstrap, RBAC, departments."""

from __future__ import annotations

import re

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


async def _register(client: AsyncClient, payload: dict) -> dict:
    reg = await client.post("/api/v1/auth/register", json=payload)
    assert reg.status_code == 201, reg.text
    code = _code_for(payload["phone"])
    verify = await client.post(
        "/api/v1/auth/verify-phone",
        json={"verification_id": reg.json()["verification_id"], "code": code},
    )
    assert verify.status_code == 200, verify.text
    return verify.json()


async def test_register_seeds_tenant_schema_with_roles_and_owner_membership(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_register_payload: dict,
):
    bundle = await _register(client, sample_register_payload)
    schema = bundle["tenant"]["schema_name"]
    assert schema.startswith("tenant_")

    # 5 standard roles seeded
    await db_session.execute(text(f"SET search_path TO {schema}, public"))
    roles = (await db_session.execute(text("SELECT slug FROM roles"))).all()
    slugs = {r[0] for r in roles}
    assert {"owner", "admin", "manager", "operator", "viewer"} <= slugs

    # Owner membership exists
    memberships = (await db_session.execute(text("SELECT user_id FROM user_memberships"))).all()
    assert len(memberships) == 1
    assert str(memberships[0][0]) == bundle["user"]["id"]
    await db_session.execute(text("SET search_path TO public"))


async def test_authenticated_endpoint_requires_bearer_token(client: AsyncClient):
    resp = await client.get("/api/v1/tenant/me")
    assert resp.status_code == 401


async def test_owner_can_read_tenant_and_list_departments(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _register(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    me = await client.get("/api/v1/tenant/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["name"] == sample_register_payload["company_name"]

    depts = await client.get("/api/v1/departments", headers=headers)
    assert depts.status_code == 200
    assert depts.json() == []


async def test_owner_can_create_and_list_departments(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _register(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    create = await client.post(
        "/api/v1/departments",
        headers=headers,
        json={"name": "Sotuv", "description": "Savdo bo'limi"},
    )
    assert create.status_code == 201, create.text
    dept = create.json()
    assert dept["name"] == "Sotuv"

    listing = await client.get("/api/v1/departments", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_owner_can_update_tenant_company_name(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _register(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    resp = await client.patch(
        "/api/v1/tenant/me",
        headers=headers,
        json={"name": "Akme Salon LLC"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Akme Salon LLC"


async def test_my_permissions_returns_full_set_for_owner(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _register(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    resp = await client.get("/api/v1/roles/me", headers=headers)
    assert resp.status_code == 200
    perms = resp.json()
    assert "tenant.update" in perms
    assert "departments.delete" in perms
    assert "billing.update" in perms


async def test_list_roles_returns_5_seeded_roles(
    client: AsyncClient, sample_register_payload: dict
):
    bundle = await _register(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    resp = await client.get("/api/v1/roles", headers=headers)
    assert resp.status_code == 200
    slugs = {r["slug"] for r in resp.json()}
    assert slugs == {"owner", "admin", "manager", "operator", "viewer"}


async def test_audit_log_records_department_create(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_register_payload: dict,
):
    bundle = await _register(client, sample_register_payload)
    headers = {"Authorization": f"Bearer {bundle['access_token']}"}

    create = await client.post(
        "/api/v1/departments",
        headers=headers,
        json={"name": "Marketing"},
    )
    assert create.status_code == 201

    schema = bundle["tenant"]["schema_name"]
    await db_session.execute(text(f"SET search_path TO {schema}, public"))
    rows = (
        await db_session.execute(
            text("SELECT action, resource_type FROM audit_log ORDER BY created_at")
        )
    ).all()
    assert any(action == "departments.create" for action, _ in rows)
    await db_session.execute(text("SET search_path TO public"))
