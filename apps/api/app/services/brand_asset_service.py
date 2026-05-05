"""Brand asset CRUD and upload helpers."""

from __future__ import annotations

import base64
from typing import Any
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import Brand, BrandAsset

ASSET_TYPES = frozenset({"logo", "image", "video", "template", "font", "color", "reference"})
MAX_ASSET_BYTES = 10_000_000

ALLOWED_UPLOAD_CONTENT_TYPES = frozenset(
    {
        "application/octet-stream",
        "application/pdf",
        "font/otf",
        "font/ttf",
        "font/woff",
        "font/woff2",
        "image/gif",
        "image/jpeg",
        "image/png",
        "image/svg+xml",
        "image/webp",
        "video/mp4",
        "video/webm",
    }
)

BRAND_ASSET_DDL = """
CREATE TABLE IF NOT EXISTS brand_assets (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id       uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    asset_type     varchar(30) NOT NULL,
    name           varchar(160) NOT NULL,
    file_url       text,
    content_type   varchar(120),
    file_size      integer NOT NULL DEFAULT 0,
    metadata       jsonb,
    is_primary     boolean NOT NULL DEFAULT false,
    created_by     uuid NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now()
)
"""


async def ensure_table(db: AsyncSession) -> None:
    """Install the new table for older tenant schemas during rollout."""
    await db.execute(text(BRAND_ASSET_DDL))
    await db.execute(
        text("CREATE INDEX IF NOT EXISTS ix_brand_assets_brand ON brand_assets(brand_id)")
    )
    await db.execute(
        text("CREATE INDEX IF NOT EXISTS ix_brand_assets_type ON brand_assets(asset_type)")
    )


def validate_asset_type(asset_type: str) -> str:
    normalized = asset_type.strip().lower()
    if normalized not in ASSET_TYPES:
        allowed = ", ".join(sorted(ASSET_TYPES))
        raise ValueError(f"Unsupported asset type. Allowed: {allowed}")
    return normalized


def _data_url(content_type: str, payload: bytes) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


async def _ensure_brand(db: AsyncSession, brand_id: UUID) -> None:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")


async def _clear_primary(
    db: AsyncSession,
    *,
    brand_id: UUID,
    asset_type: str,
    exclude_id: UUID | None = None,
) -> None:
    stmt = update(BrandAsset).where(
        BrandAsset.brand_id == brand_id,
        BrandAsset.asset_type == asset_type,
        BrandAsset.is_primary.is_(True),
    )
    if exclude_id is not None:
        stmt = stmt.where(BrandAsset.id != exclude_id)
    await db.execute(stmt.values(is_primary=False))


async def list_assets(
    db: AsyncSession,
    *,
    brand_id: UUID | None = None,
    asset_type: str | None = None,
    limit: int = 100,
) -> list[BrandAsset]:
    await ensure_table(db)
    stmt = select(BrandAsset)
    if brand_id is not None:
        stmt = stmt.where(BrandAsset.brand_id == brand_id)
    if asset_type:
        stmt = stmt.where(BrandAsset.asset_type == validate_asset_type(asset_type))
    stmt = stmt.order_by(BrandAsset.is_primary.desc(), BrandAsset.created_at.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars())


async def create_asset(
    db: AsyncSession,
    *,
    brand_id: UUID,
    asset_type: str,
    name: str,
    file_url: str | None,
    content_type: str | None,
    file_size: int,
    metadata: dict[str, Any] | None,
    is_primary: bool,
    user_id: UUID,
) -> BrandAsset:
    await ensure_table(db)
    await _ensure_brand(db, brand_id)
    normalized_type = validate_asset_type(asset_type)
    if is_primary:
        await _clear_primary(db, brand_id=brand_id, asset_type=normalized_type)

    asset = BrandAsset(
        brand_id=brand_id,
        asset_type=normalized_type,
        name=name.strip(),
        file_url=file_url,
        content_type=content_type,
        file_size=file_size,
        metadata_=metadata,
        is_primary=is_primary,
        created_by=user_id,
    )
    db.add(asset)
    await db.flush()
    return asset


async def upload_asset(
    db: AsyncSession,
    *,
    brand_id: UUID,
    asset_type: str,
    name: str,
    filename: str,
    content_type: str | None,
    payload: bytes,
    is_primary: bool,
    user_id: UUID,
) -> BrandAsset:
    if not payload:
        raise ValueError("Empty file")
    if len(payload) > MAX_ASSET_BYTES:
        raise ValueError("File is too large. Maximum size is 10 MB")

    final_content_type = content_type or "application/octet-stream"
    if final_content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
        raise ValueError("Unsupported file type")

    metadata: dict[str, Any] = {"filename": filename}
    return await create_asset(
        db,
        brand_id=brand_id,
        asset_type=asset_type,
        name=name,
        file_url=_data_url(final_content_type, payload),
        content_type=final_content_type,
        file_size=len(payload),
        metadata=metadata,
        is_primary=is_primary,
        user_id=user_id,
    )


async def update_asset(
    db: AsyncSession,
    asset_id: UUID,
    *,
    asset_type: str | None = None,
    name: str | None = None,
    file_url: str | None = None,
    content_type: str | None = None,
    file_size: int | None = None,
    metadata: dict[str, Any] | None = None,
    is_primary: bool | None = None,
) -> BrandAsset | None:
    await ensure_table(db)
    asset = await db.get(BrandAsset, asset_id)
    if asset is None:
        return None

    final_type = validate_asset_type(asset_type) if asset_type is not None else asset.asset_type
    remains_primary_with_new_type = (
        is_primary is None and asset.is_primary and final_type != asset.asset_type
    )
    if is_primary is True or remains_primary_with_new_type:
        await _clear_primary(
            db, brand_id=asset.brand_id, asset_type=final_type, exclude_id=asset.id
        )

    if asset_type is not None:
        asset.asset_type = final_type
    if name is not None:
        asset.name = name.strip()
    if file_url is not None:
        asset.file_url = file_url
    if content_type is not None:
        asset.content_type = content_type
    if file_size is not None:
        asset.file_size = file_size
    if metadata is not None:
        asset.metadata_ = metadata
    if is_primary is not None:
        asset.is_primary = is_primary

    await db.flush()
    return asset


async def delete_asset(db: AsyncSession, asset_id: UUID) -> bool:
    await ensure_table(db)
    asset = await db.get(BrandAsset, asset_id)
    if asset is None:
        return False
    await db.delete(asset)
    await db.flush()
    return True


__all__ = [
    "ASSET_TYPES",
    "MAX_ASSET_BYTES",
    "create_asset",
    "delete_asset",
    "ensure_table",
    "list_assets",
    "update_asset",
    "upload_asset",
    "validate_asset_type",
]
