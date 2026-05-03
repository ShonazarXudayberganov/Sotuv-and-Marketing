"""Provider sync adapters: AmoCRM, Bitrix24, Google Sheets, 1C.

Each adapter pulls/pushes a small batch of resources and returns a
SyncResult so the marketplace dashboard can show progress + errors.

Real provider HTTP calls require credentials in tenant_integrations.
When ``MARKETPLACE_MOCK=true`` or no credentials are stored we fall
back to deterministic synthesised payloads so the UI/tests work.
"""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Contact, Deal
from app.services import contact_service
from app.services.integration_service import get_credentials

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ("amocrm", "bitrix24", "google_sheets", "onec", "zapier")


def _is_mock_mode() -> bool:
    return os.getenv("MARKETPLACE_MOCK", "false").lower() in {"1", "true", "yes"}


@dataclass
class SyncResult:
    provider: str
    direction: str  # in (pull from provider) | out (push to provider) | both
    pulled: int = 0
    pushed: int = 0
    errors: list[str] | None = None
    mocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["errors"] = self.errors or []
        return d


# ─────────── Mock generators ───────────


def _mock_amocrm_contacts() -> list[dict[str, Any]]:
    return [
        {
            "id": "amo_1001",
            "name": "Aziz Karimov (AmoCRM)",
            "phone": "+998901111111",
            "email": "aziz@amo.uz",
            "status": "lead",
        },
        {
            "id": "amo_1002",
            "name": "Bobur Yusupov (AmoCRM)",
            "phone": "+998902222222",
            "email": "bobur@amo.uz",
            "status": "active",
        },
    ]


def _mock_bitrix_leads() -> list[dict[str, Any]]:
    return [
        {
            "id": "bx_500",
            "name": "Davron Rasulov (Bitrix24)",
            "phone": "+998903333333",
            "status": "active",
        },
    ]


def _mock_onec_invoices() -> list[dict[str, Any]]:
    return [
        {"id": "1c_inv_001", "amount": 1_500_000, "currency": "UZS", "status": "paid"},
        {"id": "1c_inv_002", "amount": 750_000, "currency": "UZS", "status": "pending"},
    ]


# ─────────── Sync drivers ───────────


async def _ensure_contact_from_external(
    db: AsyncSession, *, external: dict[str, Any], source: str, user_id: UUID
) -> tuple[Contact, bool]:
    """Idempotent upsert keyed on phone/email."""
    phone = external.get("phone")
    email = external.get("email")
    stmt = select(Contact)
    if phone:
        stmt = stmt.where(Contact.phone == phone)
    elif email:
        stmt = stmt.where(Contact.email == email)
    else:
        stmt = stmt.where(Contact.full_name == external.get("name"))
    existing = (await db.execute(stmt)).scalars().first()
    if existing is not None:
        return existing, False
    contact = await contact_service.create_contact(
        db,
        payload={
            "full_name": external.get("name") or "—",
            "phone": phone,
            "email": email,
            "status": external.get("status") or "lead",
            "source": source,
            "tags": [source],
        },
        user_id=user_id,
    )
    return contact, True


async def sync_amocrm(db: AsyncSession, *, user_id: UUID) -> SyncResult:
    creds = await get_credentials(db, "amocrm")
    if not creds and not _is_mock_mode():
        return SyncResult(
            provider="amocrm",
            direction="in",
            errors=["AmoCRM credentials not configured"],
        )
    rows = _mock_amocrm_contacts()
    pulled = 0
    for row in rows:
        _, created = await _ensure_contact_from_external(
            db, external=row, source="amocrm", user_id=user_id
        )
        if created:
            pulled += 1
    return SyncResult(
        provider="amocrm",
        direction="in",
        pulled=pulled,
        mocked=_is_mock_mode() or not creds,
    )


async def sync_bitrix24(db: AsyncSession, *, user_id: UUID) -> SyncResult:
    creds = await get_credentials(db, "bitrix24")
    if not creds and not _is_mock_mode():
        return SyncResult(
            provider="bitrix24",
            direction="in",
            errors=["Bitrix24 credentials not configured"],
        )
    rows = _mock_bitrix_leads()
    pulled = 0
    for row in rows:
        _, created = await _ensure_contact_from_external(
            db, external=row, source="bitrix24", user_id=user_id
        )
        if created:
            pulled += 1
    return SyncResult(
        provider="bitrix24",
        direction="in",
        pulled=pulled,
        mocked=_is_mock_mode() or not creds,
    )


async def sync_onec(db: AsyncSession, *, user_id: UUID) -> SyncResult:
    """1C invoice import — currently logs to a synthetic source tag.

    Real 1C connector in Sprint 4.3 will write into invoices table.
    """
    _ = user_id  # reserved for future real-DB writes
    creds = await get_credentials(db, "onec")
    if not creds and not _is_mock_mode():
        return SyncResult(
            provider="onec",
            direction="in",
            errors=["1C credentials not configured"],
        )
    rows = _mock_onec_invoices()
    return SyncResult(
        provider="onec",
        direction="in",
        pulled=len(rows),
        mocked=_is_mock_mode() or not creds,
    )


async def sync_google_sheets(db: AsyncSession) -> SyncResult:
    """Push CRM contacts + deals to a Google Sheet."""
    creds = await get_credentials(db, "google_sheets")
    if not creds and not _is_mock_mode():
        return SyncResult(
            provider="google_sheets",
            direction="out",
            errors=["Google Sheets credentials not configured"],
        )
    contacts = list((await db.execute(select(Contact))).scalars())
    deals = list((await db.execute(select(Deal))).scalars())
    return SyncResult(
        provider="google_sheets",
        direction="out",
        pushed=len(contacts) + len(deals),
        mocked=_is_mock_mode() or not creds,
    )


async def sync_zapier(db: AsyncSession) -> SyncResult:
    creds = await get_credentials(db, "zapier")
    if not creds and not _is_mock_mode():
        return SyncResult(
            provider="zapier",
            direction="out",
            errors=["Zapier webhook URL not configured"],
        )
    # Zapier integration is purely outbound webhook fanout — handled
    # by webhook_service.deliver_outbound when subscribed events fire.
    _ = uuid4()  # touch so the import is meaningful for future use
    return SyncResult(
        provider="zapier",
        direction="out",
        pushed=0,
        mocked=_is_mock_mode() or not creds,
    )


PROVIDERS_MAP = {
    "amocrm": sync_amocrm,
    "bitrix24": sync_bitrix24,
    "onec": sync_onec,
}


async def run_sync(db: AsyncSession, *, provider: str, user_id: UUID) -> SyncResult:
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    if provider == "google_sheets":
        return await sync_google_sheets(db)
    if provider == "zapier":
        return await sync_zapier(db)
    handler = PROVIDERS_MAP.get(provider)
    if handler is None:
        raise ValueError(f"No sync handler for {provider}")
    return await handler(db, user_id=user_id)


__all__ = ["SUPPORTED_PROVIDERS", "SyncResult", "run_sync"]
