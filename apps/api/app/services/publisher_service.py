"""Provider-agnostic publish dispatcher.

Routes a (post, social_account) pair to the right channel adapter:
  - telegram   -> telegram_service.send_message
  - facebook   -> meta_service.publish_facebook_post
  - instagram  -> meta_service.publish_instagram_post (needs media)
  - youtube    -> not yet (read-only in Sprint 1.5)

The result includes ``external_post_id`` (when available) — the worker
records it on the PostPublication row so the user can deep-link later.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import BrandSocialAccount, Post
from app.services import meta_service, telegram_service
from app.services.meta_service import MetaError
from app.services.telegram_service import TelegramError

logger = logging.getLogger(__name__)


class PublishError(RuntimeError):
    """Raised when an adapter fails to publish."""


class PermanentPublishError(PublishError):
    """Provider rejected the publish in a way retries cannot fix."""


class AuthenticationPublishError(PermanentPublishError):
    """Credentials are missing/expired and require reconnect or refresh."""


class UnsupportedProviderError(PublishError):
    """The provider has no publish path yet (e.g. youtube uploads)."""


@dataclass
class PublishResult:
    external_post_id: str | None
    raw: dict[str, object]
    remote_status: str = "published"


async def _publish_telegram(
    db: AsyncSession, account: BrandSocialAccount, post: Post
) -> PublishResult:
    chat_id: int | str = account.external_id
    if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
        chat_id = int(chat_id)
    try:
        result = await telegram_service.send_message(db, chat_id=chat_id, text=post.body)
    except TelegramError as exc:
        raise PublishError(str(exc)) from exc
    return PublishResult(
        external_post_id=str(result.get("message_id") or "") or None,
        raw=dict(result),
    )


async def _publish_facebook(
    db: AsyncSession, account: BrandSocialAccount, post: Post
) -> PublishResult:
    meta = account.metadata_ or {}
    page_token = meta.get("page_token")
    if not page_token:
        raise AuthenticationPublishError("Page access token missing — relink the account")
    try:
        result = await meta_service.publish_facebook_post(
            db,
            page_id=account.external_id,
            page_access_token=str(page_token),
            message=post.body,
        )
    except MetaError as exc:
        if exc.is_auth:
            refreshed = await meta_service.refresh_page_token(db, page_id=account.external_id)
            if refreshed and refreshed != page_token:
                account.metadata_ = {**meta, "page_token": refreshed}
                try:
                    result = await meta_service.publish_facebook_post(
                        db,
                        page_id=account.external_id,
                        page_access_token=refreshed,
                        message=post.body,
                    )
                except MetaError as retry_exc:
                    raise _meta_publish_error(retry_exc) from retry_exc
            else:
                raise AuthenticationPublishError(str(exc)) from exc
        else:
            raise _meta_publish_error(exc) from exc
    return PublishResult(
        external_post_id=str(result.get("id") or "") or None,
        raw=dict(result),
    )


async def _publish_instagram(
    db: AsyncSession, account: BrandSocialAccount, post: Post
) -> PublishResult:
    meta = account.metadata_ or {}
    page_token = meta.get("page_token")
    if not page_token:
        raise AuthenticationPublishError("Page access token missing — relink the account")
    media_list = post.media_urls or []
    media = media_list[0] if media_list else None
    if not media:
        raise PermanentPublishError("Instagram requires at least one media_url")
    try:
        result = await meta_service.publish_instagram_post(
            db,
            ig_user_id=account.external_id,
            page_access_token=str(page_token),
            image_url=str(media),
            caption=post.body,
        )
    except MetaError as exc:
        if exc.is_auth:
            page_id = str(meta.get("page_id") or "")
            refreshed = (
                await meta_service.refresh_page_token(db, page_id=page_id) if page_id else None
            )
            if refreshed and refreshed != page_token:
                account.metadata_ = {**meta, "page_token": refreshed}
                try:
                    result = await meta_service.publish_instagram_post(
                        db,
                        ig_user_id=account.external_id,
                        page_access_token=refreshed,
                        image_url=str(media),
                        caption=post.body,
                    )
                except MetaError as retry_exc:
                    raise _meta_publish_error(retry_exc) from retry_exc
            else:
                raise AuthenticationPublishError(str(exc)) from exc
        else:
            raise _meta_publish_error(exc) from exc
    return PublishResult(
        external_post_id=str(result.get("id") or "") or None,
        raw=dict(result),
    )


PROVIDER_DISPATCH = {
    "telegram": _publish_telegram,
    "facebook": _publish_facebook,
    "instagram": _publish_instagram,
}


def _meta_publish_error(exc: MetaError) -> PublishError:
    if exc.is_auth:
        return AuthenticationPublishError(str(exc))
    if exc.is_transient:
        return PublishError(str(exc))
    return PermanentPublishError(str(exc))


async def publish(db: AsyncSession, *, account: BrandSocialAccount, post: Post) -> PublishResult:
    handler = PROVIDER_DISPATCH.get(account.provider)
    if handler is None:
        raise UnsupportedProviderError(f"Publishing to {account.provider} is not supported yet")
    return await handler(db, account, post)


__all__ = [
    "PROVIDER_DISPATCH",
    "AuthenticationPublishError",
    "PermanentPublishError",
    "PublishError",
    "PublishResult",
    "UnsupportedProviderError",
    "publish",
]
