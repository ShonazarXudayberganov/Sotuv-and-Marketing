from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.smm import Brand
from app.schemas.smm import BrandCreate, BrandOut, BrandUpdate
from app.services import audit_service
from app.services.brand_service import generate_unique_slug, set_default

router = APIRouter()


@router.get("", response_model=list[BrandOut])
async def list_brands(
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[Brand]:
    rows = (
        await db.execute(
            select(Brand)
            .where(Brand.is_active.is_(True))
            .order_by(Brand.is_default.desc(), Brand.created_at.desc())
        )
    ).scalars()
    return list(rows)


@router.post("", response_model=BrandOut, status_code=201)
async def create_brand(
    payload: BrandCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Brand:
    slug = await generate_unique_slug(db, payload.name)
    brand = Brand(
        name=payload.name,
        slug=slug,
        description=payload.description,
        industry=payload.industry,
        logo_url=payload.logo_url,
        primary_color=payload.primary_color,
        voice_tone=payload.voice_tone,
        target_audience=payload.target_audience,
        languages=payload.languages,
        is_default=payload.is_default,
        created_by=current.id,
    )
    db.add(brand)
    await db.flush()

    if payload.is_default:
        await set_default(db, brand.id)

    await audit_service.record(
        db,
        user_id=current.id,
        action="brands.create",
        resource_type="brand",
        resource_id=str(brand.id),
        metadata={"name": brand.name, "slug": brand.slug},
        request=request,
    )
    await db.commit()
    return brand


@router.get("/{brand_id}", response_model=BrandOut)
async def get_brand(
    brand_id: UUID,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Brand:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.patch("/{brand_id}", response_model=BrandOut)
async def update_brand(
    brand_id: UUID,
    payload: BrandUpdate,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Brand:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    fields = payload.model_dump(exclude_none=True)
    for f, v in fields.items():
        setattr(brand, f, v)
    await db.flush()
    await audit_service.record(
        db,
        user_id=current.id,
        action="brands.update",
        resource_type="brand",
        resource_id=str(brand.id),
        metadata=fields,
        request=request,
    )
    await db.commit()
    return brand


@router.post("/{brand_id}/set-default", response_model=BrandOut)
async def make_default(
    brand_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Brand:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    await set_default(db, brand_id)
    await audit_service.record(
        db,
        user_id=current.id,
        action="brands.set_default",
        resource_type="brand",
        resource_id=str(brand_id),
        request=request,
    )
    await db.commit()
    refreshed = await db.get(Brand, brand_id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return refreshed


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, str]:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    await db.delete(brand)
    await audit_service.record(
        db,
        user_id=current.id,
        action="brands.delete",
        resource_type="brand",
        resource_id=str(brand_id),
        request=request,
    )
    await db.commit()
    return {"status": "deleted"}
