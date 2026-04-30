"""Brand-scoped social account links (Telegram channels, IG profiles, FB pages…).

The bot/app credentials live in ``tenant_integrations`` (one set per tenant);
each brand can attach multiple external accounts that use those credentials.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import Brand, BrandSocialAccount


async def list_for_brand(
    db: AsyncSession,
    *,
    brand_id: UUID,
    provider: str | None = None,
) -> list[BrandSocialAccount]:
    stmt = select(BrandSocialAccount).where(BrandSocialAccount.brand_id == brand_id)
    if provider is not None:
        stmt = stmt.where(BrandSocialAccount.provider == provider)
    stmt = stmt.order_by(BrandSocialAccount.created_at.desc())
    return list((await db.execute(stmt)).scalars())


async def list_for_tenant(
    db: AsyncSession,
    *,
    provider: str | None = None,
) -> list[BrandSocialAccount]:
    stmt = select(BrandSocialAccount)
    if provider is not None:
        stmt = stmt.where(BrandSocialAccount.provider == provider)
    stmt = stmt.order_by(BrandSocialAccount.created_at.desc())
    return list((await db.execute(stmt)).scalars())


async def upsert(
    db: AsyncSession,
    *,
    brand_id: UUID,
    provider: str,
    external_id: str,
    external_handle: str | None,
    external_name: str | None,
    chat_type: str | None,
    metadata: dict[str, Any] | None,
    user_id: UUID,
) -> BrandSocialAccount:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")

    existing = (
        (
            await db.execute(
                select(BrandSocialAccount).where(
                    BrandSocialAccount.brand_id == brand_id,
                    BrandSocialAccount.provider == provider,
                    BrandSocialAccount.external_id == external_id,
                )
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        existing.external_handle = external_handle
        existing.external_name = external_name
        existing.chat_type = chat_type
        existing.metadata_ = metadata
        existing.is_active = True
        existing.last_error = None
        await db.flush()
        return existing

    rec = BrandSocialAccount(
        brand_id=brand_id,
        provider=provider,
        external_id=external_id,
        external_handle=external_handle,
        external_name=external_name,
        chat_type=chat_type,
        metadata_=metadata,
        created_by=user_id,
        is_active=True,
    )
    db.add(rec)
    await db.flush()
    return rec


async def get(db: AsyncSession, account_id: UUID) -> BrandSocialAccount | None:
    return await db.get(BrandSocialAccount, account_id)


async def remove(db: AsyncSession, account_id: UUID) -> bool:
    rec = await db.get(BrandSocialAccount, account_id)
    if rec is None:
        return False
    await db.delete(rec)
    await db.flush()
    return True


async def mark_published(
    db: AsyncSession,
    account_id: UUID,
    *,
    error: str | None = None,
) -> None:
    rec = await db.get(BrandSocialAccount, account_id)
    if rec is None:
        return
    if error is None:
        rec.last_published_at = datetime.now(UTC)
        rec.last_error = None
    else:
        rec.last_error = error[:500]
    await db.flush()


__all__ = [
    "get",
    "list_for_brand",
    "list_for_tenant",
    "mark_published",
    "remove",
    "upsert",
]
