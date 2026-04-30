"""Brand-scoped social account management.

Sprint 1.3 covers Telegram. Future sprints add Instagram/Facebook/YouTube here.
"""

from __future__ import annotations

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.models.smm import BrandSocialAccount
from app.schemas.social import (
    SocialAccountOut,
    TelegramBotInfo,
    TelegramLinkRequest,
    TelegramSendResult,
    TelegramTestRequest,
)
from app.services import (
    audit_service,
    social_account_service,
    telegram_service,
)
from app.services.telegram_service import TelegramError

router = APIRouter()


def _is_telegram_mock() -> bool:
    return os.getenv("TELEGRAM_MOCK", "false").lower() in {"1", "true", "yes"}


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
