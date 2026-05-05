from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.smm import BrandAsset
from app.schemas.brand_asset import BrandAssetCreate, BrandAssetOut, BrandAssetUpdate
from app.services import audit_service, brand_asset_service

router = APIRouter()
brand_router = APIRouter()


def _out(asset: BrandAsset) -> BrandAssetOut:
    return BrandAssetOut(
        id=asset.id,
        brand_id=asset.brand_id,
        asset_type=asset.asset_type,
        name=asset.name,
        file_url=asset.file_url,
        content_type=asset.content_type,
        file_size=asset.file_size,
        metadata=asset.metadata_,
        is_primary=asset.is_primary,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


async def _upload(
    *,
    request: Request,
    brand_id: UUID,
    asset_type: str,
    name: str,
    is_primary: bool,
    file: UploadFile,
    current: CurrentUser,
    db: AsyncSession,
) -> BrandAssetOut:
    contents = await file.read()
    try:
        asset = await brand_asset_service.upload_asset(
            db,
            brand_id=brand_id,
            asset_type=asset_type,
            name=name,
            filename=file.filename or name,
            content_type=file.content_type,
            payload=contents,
            is_primary=is_primary,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="brand_assets.upload",
        resource_type="brand_asset",
        resource_id=str(asset.id),
        metadata={
            "brand_id": str(brand_id),
            "asset_type": asset.asset_type,
            "filename": file.filename,
            "file_size": asset.file_size,
        },
        request=request,
    )
    await db.commit()
    return _out(asset)


@router.get("", response_model=list[BrandAssetOut])
async def list_assets(
    brand_id: UUID | None = None,
    asset_type: str | None = None,
    limit: int = 100,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[BrandAssetOut]:
    try:
        assets = await brand_asset_service.list_assets(
            db, brand_id=brand_id, asset_type=asset_type, limit=min(limit, 200)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_out(asset) for asset in assets]


@router.post("", response_model=BrandAssetOut, status_code=201)
async def create_asset(
    payload: BrandAssetCreate,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> BrandAssetOut:
    try:
        asset = await brand_asset_service.create_asset(
            db,
            brand_id=payload.brand_id,
            asset_type=payload.asset_type,
            name=payload.name,
            file_url=payload.file_url,
            content_type=payload.content_type,
            file_size=payload.file_size,
            metadata=payload.metadata,
            is_primary=payload.is_primary,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="brand_assets.create",
        resource_type="brand_asset",
        resource_id=str(asset.id),
        metadata={"brand_id": str(asset.brand_id), "asset_type": asset.asset_type},
        request=request,
    )
    await db.commit()
    return _out(asset)


@router.post("/upload", response_model=BrandAssetOut, status_code=201)
async def upload_asset(
    request: Request,
    brand_id: UUID = Form(...),
    asset_type: str = Form(...),
    name: str = Form(...),
    is_primary: bool = Form(False),
    file: UploadFile = File(...),
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> BrandAssetOut:
    return await _upload(
        request=request,
        brand_id=brand_id,
        asset_type=asset_type,
        name=name,
        is_primary=is_primary,
        file=file,
        current=current,
        db=db,
    )


@router.patch("/{asset_id}", response_model=BrandAssetOut)
async def update_asset(
    asset_id: UUID,
    payload: BrandAssetUpdate,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> BrandAssetOut:
    try:
        asset = await brand_asset_service.update_asset(
            db,
            asset_id,
            asset_type=payload.asset_type,
            name=payload.name,
            file_url=payload.file_url,
            content_type=payload.content_type,
            file_size=payload.file_size,
            metadata=payload.metadata,
            is_primary=payload.is_primary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    await audit_service.record(
        db,
        user_id=current.id,
        action="brand_assets.update",
        resource_type="brand_asset",
        resource_id=str(asset.id),
        request=request,
    )
    await db.commit()
    return _out(asset)


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    deleted = await brand_asset_service.delete_asset(db, asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="brand_assets.delete",
        resource_type="brand_asset",
        resource_id=str(asset_id),
        request=request,
    )
    await db.commit()
    return {"deleted": True}


@brand_router.get("/{brand_id}/assets", response_model=list[BrandAssetOut])
async def list_brand_assets(
    brand_id: UUID,
    asset_type: str | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[BrandAssetOut]:
    try:
        assets = await brand_asset_service.list_assets(db, brand_id=brand_id, asset_type=asset_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_out(asset) for asset in assets]


@brand_router.post("/{brand_id}/assets", response_model=BrandAssetOut, status_code=201)
async def upload_brand_asset(
    request: Request,
    brand_id: UUID,
    asset_type: str = Form(...),
    name: str = Form(...),
    is_primary: bool = Form(False),
    file: UploadFile = File(...),
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> BrandAssetOut:
    return await _upload(
        request=request,
        brand_id=brand_id,
        asset_type=asset_type,
        name=name,
        is_primary=is_primary,
        file=file,
        current=current,
        db=db,
    )


@brand_router.delete("/{brand_id}/assets/{asset_id}")
async def delete_brand_asset(
    brand_id: UUID,
    asset_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    await brand_asset_service.ensure_table(db)
    asset = await db.get(BrandAsset, asset_id)
    if asset is None or asset.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    return await delete_asset(asset_id=asset_id, request=request, current=current, db=db)
