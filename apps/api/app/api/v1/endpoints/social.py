"""Brand-scoped social account management.

Sprint 1.3 covers Telegram. Future sprints add Instagram/Facebook/YouTube here.
"""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.smm import BrandSocialAccount
from app.schemas.social import (
    MetaLinkRequest,
    MetaPageOption,
    MetaSendResult,
    MetaTestRequest,
    SocialAccountOut,
    TelegramBotInfo,
    TelegramLinkRequest,
    TelegramSendResult,
    TelegramTestRequest,
)
from app.services import (
    audit_service,
    meta_service,
    social_account_service,
    telegram_service,
)
from app.services.meta_service import MetaError
from app.services.telegram_service import TelegramError

router = APIRouter()


def _is_telegram_mock() -> bool:
    return os.getenv("TELEGRAM_MOCK", "false").lower() in {"1", "true", "yes"}


def _is_meta_mock() -> bool:
    return os.getenv("META_MOCK", "false").lower() in {"1", "true", "yes"}


@router.get("/accounts", response_model=list[SocialAccountOut])
async def list_accounts(
    brand_id: UUID | None = None,
    provider: str | None = None,
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[BrandSocialAccount]:
    if brand_id is None:
        return await social_account_service.list_for_tenant(db, provider=provider)
    return await social_account_service.list_for_brand(db, brand_id=brand_id, provider=provider)


@router.delete("/accounts/{account_id}")
async def remove_account(
    account_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, bool]:
    rec = await social_account_service.get(db, account_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Account not found")
    await social_account_service.remove(db, account_id)
    await audit_service.record(
        db,
        user_id=current.id,
        action="social.unlink",
        resource_type="social_account",
        resource_id=str(account_id),
        metadata={"provider": rec.provider, "brand_id": str(rec.brand_id)},
        request=request,
    )
    await db.commit()
    return {"deleted": True}


@router.get("/telegram/bot-info", response_model=TelegramBotInfo)
async def telegram_bot_info(
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> TelegramBotInfo:
    try:
        info = await telegram_service.get_me(db)
    except TelegramError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TelegramBotInfo(
        username=info.get("username"),
        first_name=info.get("first_name"),
        bot_id=info.get("id"),
        can_join_groups=info.get("can_join_groups"),
        mocked=_is_telegram_mock(),
    )


@router.post("/telegram/link", response_model=SocialAccountOut, status_code=201)
async def telegram_link_channel(
    payload: TelegramLinkRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> BrandSocialAccount:
    try:
        chat = await telegram_service.get_chat(db, payload.chat)
    except TelegramError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        rec = await social_account_service.upsert(
            db,
            brand_id=payload.brand_id,
            provider="telegram",
            external_id=str(chat.get("id")),
            external_handle=chat.get("username"),
            external_name=chat.get("title") or chat.get("username"),
            chat_type=chat.get("type"),
            metadata={"raw_chat": chat},
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="social.link",
        resource_type="social_account",
        resource_id=str(rec.id),
        metadata={
            "provider": "telegram",
            "brand_id": str(payload.brand_id),
            "chat": payload.chat,
        },
        request=request,
    )
    rec_id = rec.id
    await db.commit()
    fresh = await db.get(BrandSocialAccount, rec_id)
    if fresh is None:
        raise HTTPException(status_code=500, detail="Account vanished after commit")
    return fresh


@router.post("/telegram/test", response_model=TelegramSendResult)
async def telegram_send_test(
    payload: TelegramTestRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> TelegramSendResult:
    rec = await social_account_service.get(db, payload.account_id)
    if rec is None or rec.provider != "telegram":
        raise HTTPException(status_code=404, detail="Telegram account not found")

    chat_id: int | str = rec.external_id
    if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
        chat_id = int(chat_id)

    try:
        result = await telegram_service.send_message(db, chat_id=chat_id, text=payload.text)
        await social_account_service.mark_published(db, rec.id)
    except TelegramError as exc:
        await social_account_service.mark_published(db, rec.id, error=str(exc))
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="social.test_send",
        resource_type="social_account",
        resource_id=str(rec.id),
        metadata={"provider": "telegram", "chars": len(payload.text)},
        request=request,
    )
    await db.commit()
    return TelegramSendResult(
        message_id=int(result.get("message_id", 0)),
        chat_id=chat_id,
        sent_text=payload.text,
        mocked=_is_telegram_mock(),
    )


# ─────────── Meta (Facebook + Instagram) ───────────


@router.get("/meta/pages", response_model=list[MetaPageOption])
async def meta_list_pages(
    _: CurrentUser = Depends(require_permission("smm.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[MetaPageOption]:
    try:
        pages = await meta_service.list_pages(db)
    except MetaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    out: list[MetaPageOption] = []
    for p in pages:
        ig: dict[str, Any] | None
        try:
            ig = await meta_service.get_instagram_business_account(
                db, page_id=str(p["id"]), page_token=p.get("access_token")
            )
        except MetaError:
            ig = None
        out.append(
            MetaPageOption(
                id=str(p["id"]),
                name=str(p.get("name") or "—"),
                category=p.get("category"),
                has_instagram=ig is not None,
                instagram_username=(ig or {}).get("username"),
            )
        )
    return out


@router.post("/meta/link", response_model=SocialAccountOut, status_code=201)
async def meta_link_page(
    payload: MetaLinkRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> BrandSocialAccount:
    try:
        pages = await meta_service.list_pages(db)
    except MetaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    page = next((p for p in pages if str(p.get("id")) == payload.page_id), None)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found in connected Meta app")

    page_token = page.get("access_token")

    if payload.target == "instagram":
        try:
            ig = await meta_service.get_instagram_business_account(
                db, page_id=payload.page_id, page_token=page_token
            )
        except MetaError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if ig is None:
            raise HTTPException(
                status_code=400, detail="This Page is not linked to an IG Business account"
            )
        provider = "instagram"
        external_id = str(ig["id"])
        external_handle = ig.get("username")
        external_name = ig.get("name") or ig.get("username")
        chat_type = "business"
        metadata: dict[str, Any] = {
            "page_id": payload.page_id,
            "page_token": page_token,
            "ig": ig,
        }
    else:
        provider = "facebook"
        external_id = payload.page_id
        external_handle = None
        external_name = page.get("name")
        chat_type = "page"
        metadata = {"page_token": page_token, "raw_page": page}

    try:
        rec = await social_account_service.upsert(
            db,
            brand_id=payload.brand_id,
            provider=provider,
            external_id=external_id,
            external_handle=external_handle,
            external_name=external_name,
            chat_type=chat_type,
            metadata=metadata,
            user_id=current.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="social.link",
        resource_type="social_account",
        resource_id=str(rec.id),
        metadata={"provider": provider, "brand_id": str(payload.brand_id)},
        request=request,
    )
    rec_id = rec.id
    await db.commit()
    fresh = await db.get(BrandSocialAccount, rec_id)
    if fresh is None:
        raise HTTPException(status_code=500, detail="Account vanished after commit")
    return fresh


@router.post("/meta/test", response_model=MetaSendResult)
async def meta_send_test(
    payload: MetaTestRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("smm.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> MetaSendResult:
    rec = await social_account_service.get(db, payload.account_id)
    if rec is None or rec.provider not in {"facebook", "instagram"}:
        raise HTTPException(status_code=404, detail="Meta account not found")

    meta = rec.metadata_ or {}
    page_token = meta.get("page_token")
    if not page_token:
        raise HTTPException(status_code=400, detail="Page access token missing — relink account")

    try:
        if rec.provider == "facebook":
            result = await meta_service.publish_facebook_post(
                db,
                page_id=rec.external_id,
                page_access_token=str(page_token),
                message=payload.text,
            )
        else:
            if not payload.image_url:
                raise HTTPException(
                    status_code=400, detail="Instagram requires image_url for test publish"
                )
            result = await meta_service.publish_instagram_post(
                db,
                ig_user_id=rec.external_id,
                page_access_token=str(page_token),
                image_url=payload.image_url,
                caption=payload.text,
            )
        await social_account_service.mark_published(db, rec.id)
    except MetaError as exc:
        await social_account_service.mark_published(db, rec.id, error=str(exc))
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="social.test_send",
        resource_type="social_account",
        resource_id=str(rec.id),
        metadata={"provider": rec.provider, "chars": len(payload.text)},
        request=request,
    )
    await db.commit()
    return MetaSendResult(
        post_id=str(result.get("id") or result.get("post_id") or ""),
        sent_text=payload.text,
        target=rec.provider,
        mocked=_is_meta_mock(),
    )
