"""Brand lifecycle: create, update, slug uniqueness, default-brand handling."""

from __future__ import annotations

import re
import unicodedata
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import Brand


def slugify_brand(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return (slug or "brand")[:60]


async def generate_unique_slug(db: AsyncSession, name: str) -> str:
    base = slugify_brand(name)
    candidate = base
    suffix = 0
    while True:
        existing = (
            (await db.execute(select(Brand).where(Brand.slug == candidate))).scalars().first()
        )
        if existing is None:
            return candidate
        suffix += 1
        candidate = f"{base}-{suffix}"


async def set_default(db: AsyncSession, brand_id: UUID) -> None:
    await db.execute(update(Brand).values(is_default=False))
    await db.execute(update(Brand).where(Brand.id == brand_id).values(is_default=True))
    await db.flush()


async def ensure_default_exists(db: AsyncSession, *, fallback_name: str, user_id: UUID) -> Brand:
    """Used during onboarding — create a default brand from the tenant company name."""
    existing = (await db.execute(select(Brand).where(Brand.is_default.is_(True)))).scalars().first()
    if existing is not None:
        return existing

    slug = await generate_unique_slug(db, fallback_name)
    brand = Brand(
        name=fallback_name,
        slug=slug,
        is_default=True,
        is_active=True,
        languages=["uz"],
        created_by=user_id,
    )
    db.add(brand)
    await db.flush()
    return brand
