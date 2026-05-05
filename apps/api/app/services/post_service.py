"""Post lifecycle: draft -> scheduled -> publishing -> published / failed.

Run mode 1 (sync): publish_now() — invoked by the API endpoint or the worker
sweep; iterates publications, calls the publisher_service, updates rows.

Run mode 2 (sweep): claim_due_posts() locks posts with scheduled_at <= now()
into 'publishing' atomically so concurrent workers can't double-publish.

Retry backoff: 5min -> 30min -> 1h -> failed (matches docs/modules/02-smm.md).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import (
    Brand,
    BrandSocialAccount,
    ContentDraft,
    Post,
    PostPublication,
    PostPublicationEvent,
)
from app.services import publisher_service
from app.services.publisher_service import (
    AuthenticationPublishError,
    PermanentPublishError,
    PublishError,
    UnsupportedProviderError,
)

# Retry plan (cumulative): attempt 0 + 3 retries.
RETRY_DELAYS_MINUTES = (5, 30, 60)
MAX_ATTEMPTS = len(RETRY_DELAYS_MINUTES) + 1  # 4 total attempts

PENDING_PUBLICATION_STATUSES = {"pending", "publishing"}


def _now() -> datetime:
    return datetime.now(UTC)


def _next_retry_at(attempts: int) -> datetime | None:
    """attempts=1 -> +5min; attempts=2 -> +30min; attempts=3 -> +60min; else None."""
    if attempts < 1 or attempts > len(RETRY_DELAYS_MINUTES):
        return None
    return _now() + timedelta(minutes=RETRY_DELAYS_MINUTES[attempts - 1])


PUBLISH_HARDENING_DDL: tuple[str, ...] = (
    """
    ALTER TABLE IF EXISTS post_publications
        ADD COLUMN IF NOT EXISTS last_attempt_at timestamptz
    """,
    """
    ALTER TABLE IF EXISTS post_publications
        ADD COLUMN IF NOT EXISTS remote_status varchar(40)
    """,
    """
    ALTER TABLE IF EXISTS post_publications
        ADD COLUMN IF NOT EXISTS last_checked_at timestamptz
    """,
    """
    ALTER TABLE IF EXISTS post_publications
        ADD COLUMN IF NOT EXISTS permanent_failure boolean NOT NULL DEFAULT false
    """,
    """
    CREATE TABLE IF NOT EXISTS post_publication_events (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        publication_id  uuid NOT NULL REFERENCES post_publications(id) ON DELETE CASCADE,
        post_id         uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        provider        varchar(30) NOT NULL,
        event_type      varchar(40) NOT NULL,
        status          varchar(40),
        message         varchar(1000),
        metadata        jsonb,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_publication_events_publication
        ON post_publication_events(publication_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_publication_events_post
        ON post_publication_events(post_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_publication_events_type
        ON post_publication_events(event_type)
    """,
)


async def ensure_publish_schema(db: AsyncSession) -> None:
    """Self-heal existing tenant schemas after publish hardening columns land."""
    for ddl in PUBLISH_HARDENING_DDL:
        await db.execute(text(ddl))


async def record_publication_event(
    db: AsyncSession,
    publication: PostPublication,
    *,
    event_type: str,
    message: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    now = _now()
    db.add(
        PostPublicationEvent(
            publication_id=publication.id,
            post_id=publication.post_id,
            provider=publication.provider,
            event_type=event_type,
            status=publication.status,
            message=message[:1000] if message else None,
            metadata_=metadata,
            created_at=now,
            updated_at=now,
        )
    )
    await db.flush()


def _is_permanent(exc: PublishError) -> bool:
    return isinstance(
        exc,
        UnsupportedProviderError | PermanentPublishError | AuthenticationPublishError,
    )


def _roll_up_post_status(post: Post, publications: Sequence[PostPublication]) -> None:
    pending = [p for p in publications if p.status in PENDING_PUBLICATION_STATUSES]
    published = [p for p in publications if p.status == "published"]
    failed = [p for p in publications if p.status == "failed"]

    if pending:
        retry_times = [p.next_retry_at for p in pending if p.next_retry_at is not None]
        post.status = "scheduled"
        post.scheduled_at = min(retry_times) if retry_times else _now()
        post.last_error = "Some platforms are waiting for retry" if failed or published else None
        return

    if published and failed:
        post.status = "partial"
        post.last_error = "Some platforms failed; others succeeded"
        post.published_at = post.published_at or _now()
        return

    if failed and len(failed) == len(publications):
        post.status = "failed"
        post.last_error = "All platforms failed after maximum retries"
        return

    if published and len(published) == len(publications):
        post.status = "published"
        post.published_at = post.published_at or _now()
        post.last_error = None


async def create_post(
    db: AsyncSession,
    *,
    brand_id: UUID,
    body: str,
    title: str | None,
    media_urls: list[str] | None,
    social_account_ids: Sequence[UUID],
    scheduled_at: datetime | None,
    user_id: UUID,
    draft_id: UUID | None = None,
) -> Post:
    await ensure_publish_schema(db)
    if not body.strip():
        raise ValueError("Post body is empty")
    if not social_account_ids:
        raise ValueError("At least one social account is required")
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise ValueError("Brand not found")

    # Validate every account belongs to this brand.
    accounts: list[BrandSocialAccount] = []
    for acc_id in social_account_ids:
        acc = await db.get(BrandSocialAccount, acc_id)
        if acc is None or acc.brand_id != brand_id:
            raise ValueError(f"Social account {acc_id} not found for brand")
        if not acc.is_active:
            raise ValueError(f"Social account {acc_id} is inactive")
        accounts.append(acc)

    if draft_id is not None:
        draft = await db.get(ContentDraft, draft_id)
        if draft is None or draft.brand_id != brand_id:
            raise ValueError("Draft not found for brand")

    # status = scheduled if scheduled_at is set; otherwise draft.
    status = "scheduled" if scheduled_at is not None else "draft"

    post = Post(
        brand_id=brand_id,
        draft_id=draft_id,
        title=title,
        body=body,
        media_urls=media_urls or None,
        status=status,
        scheduled_at=scheduled_at,
        created_by=user_id,
    )
    db.add(post)
    await db.flush()

    for acc in accounts:
        db.add(
            PostPublication(
                post_id=post.id,
                social_account_id=acc.id,
                provider=acc.provider,
                status="pending",
            )
        )
    await db.flush()
    return post


async def list_posts(
    db: AsyncSession,
    *,
    brand_id: UUID | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Post]:
    stmt = select(Post).order_by(desc(Post.created_at)).limit(limit)
    if brand_id is not None:
        stmt = stmt.where(Post.brand_id == brand_id)
    if status is not None:
        stmt = stmt.where(Post.status == status)
    return list((await db.execute(stmt)).scalars())


async def get_post(db: AsyncSession, post_id: UUID) -> Post | None:
    return await db.get(Post, post_id)


async def list_publications(db: AsyncSession, post_id: UUID) -> list[PostPublication]:
    await ensure_publish_schema(db)
    stmt = (
        select(PostPublication)
        .where(PostPublication.post_id == post_id)
        .order_by(PostPublication.created_at)
    )
    return list((await db.execute(stmt)).scalars())


async def list_publication_events(
    db: AsyncSession,
    publication_id: UUID,
    *,
    limit: int = 10,
) -> list[PostPublicationEvent]:
    await ensure_publish_schema(db)
    stmt = (
        select(PostPublicationEvent)
        .where(PostPublicationEvent.publication_id == publication_id)
        .order_by(desc(PostPublicationEvent.created_at))
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars())


async def cancel(db: AsyncSession, post_id: UUID) -> Post | None:
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status not in {"draft", "scheduled", "review", "approved", "rejected"}:
        raise ValueError(f"Cannot cancel a post in status '{post.status}'")
    post.status = "cancelled"
    await db.flush()
    return post


async def reschedule(db: AsyncSession, post_id: UUID, scheduled_at: datetime | None) -> Post | None:
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status not in {"draft", "scheduled", "approved"}:
        raise ValueError(f"Cannot reschedule a post in status '{post.status}'")
    post.scheduled_at = scheduled_at
    post.status = (
        "scheduled"
        if scheduled_at is not None
        else "approved"
        if post.status == "approved"
        else "draft"
    )
    await db.flush()
    return post


async def submit_for_review(db: AsyncSession, post_id: UUID) -> Post | None:
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status not in {"draft", "rejected"}:
        raise ValueError(f"Cannot submit a post in status '{post.status}' for review")
    post.status = "review"
    post.last_error = None
    await db.flush()
    return post


async def approve(
    db: AsyncSession,
    post_id: UUID,
    *,
    scheduled_at: datetime | None = None,
) -> Post | None:
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status != "review":
        raise ValueError(f"Cannot approve a post in status '{post.status}'")
    post.scheduled_at = scheduled_at
    post.status = "scheduled" if scheduled_at is not None else "approved"
    post.last_error = None
    await db.flush()
    return post


async def reject(db: AsyncSession, post_id: UUID, *, reason: str) -> Post | None:
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status != "review":
        raise ValueError(f"Cannot reject a post in status '{post.status}'")
    post.status = "rejected"
    post.last_error = reason.strip()[:1000]
    await db.flush()
    return post


async def claim_due_posts(db: AsyncSession, limit: int = 25) -> list[Post]:
    """Atomically flip due posts to 'publishing' so only one worker runs them."""
    now = _now()
    id_stmt = (
        select(Post.id)
        .where(Post.status == "scheduled", Post.scheduled_at <= now)
        .order_by(Post.scheduled_at)
        .limit(limit)
    )
    ids = list((await db.execute(id_stmt)).scalars())
    if not ids:
        return []
    stmt = (
        update(Post)
        .where(Post.id.in_(ids), Post.status == "scheduled")
        .values(status="publishing")
        .returning(Post.id)
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    claimed_ids = [row[0] for row in result.fetchall()]
    if not claimed_ids:
        return []
    fetched = await db.execute(select(Post).where(Post.id.in_(claimed_ids)))
    return list(fetched.scalars())


async def publish_now(db: AsyncSession, post: Post, *, force: bool = True) -> Post:
    """Run all pending publications for a post and persist outcomes."""
    await ensure_publish_schema(db)
    post.status = "publishing"
    await db.flush()

    pubs = await list_publications(db, post.id)

    for pub in pubs:
        if pub.status in {"published", "skipped"}:
            continue
        if (
            not force
            and pub.status == "pending"
            and pub.next_retry_at is not None
            and pub.next_retry_at > _now()
        ):
            continue
        account = await db.get(BrandSocialAccount, pub.social_account_id)
        if account is None or not account.is_active:
            pub.status = "failed"
            pub.permanent_failure = True
            pub.last_error = (
                "Linked social account no longer exists"
                if account is None
                else "Linked social account is inactive"
            )
            pub.completed_at = _now()
            await record_publication_event(
                db,
                pub,
                event_type="publish_failed",
                message=pub.last_error,
                metadata={"permanent": True},
            )
            continue

        pub.attempts += 1
        pub.status = "publishing"
        pub.last_attempt_at = _now()
        pub.last_error = None
        pub.remote_status = None
        await record_publication_event(
            db,
            pub,
            event_type="publish_attempt",
            message=f"Attempt {pub.attempts}",
            metadata={"attempt": pub.attempts},
        )
        try:
            result = await publisher_service.publish(db, account=account, post=post)
        except PublishError as exc:
            pub.last_error = str(exc)[:1000]
            if _is_permanent(exc) or pub.attempts >= MAX_ATTEMPTS:
                pub.status = "failed"
                pub.permanent_failure = _is_permanent(exc)
                pub.completed_at = _now()
                pub.next_retry_at = None
                if account is not None:
                    account.last_error = pub.last_error[:500]
                await record_publication_event(
                    db,
                    pub,
                    event_type="publish_failed",
                    message=pub.last_error,
                    metadata={
                        "attempt": pub.attempts,
                        "permanent": pub.permanent_failure,
                    },
                )
            else:
                pub.status = "pending"
                pub.permanent_failure = False
                pub.next_retry_at = _next_retry_at(pub.attempts)
                await record_publication_event(
                    db,
                    pub,
                    event_type="retry_scheduled",
                    message=pub.last_error,
                    metadata={
                        "attempt": pub.attempts,
                        "next_retry_at": pub.next_retry_at.isoformat()
                        if pub.next_retry_at
                        else None,
                    },
                )
            continue

        pub.status = "published"
        pub.external_post_id = result.external_post_id
        pub.remote_status = result.remote_status
        pub.last_checked_at = _now()
        pub.permanent_failure = False
        pub.last_error = None
        pub.next_retry_at = None
        pub.completed_at = _now()
        account.last_published_at = _now()
        account.last_error = None
        await record_publication_event(
            db,
            pub,
            event_type="published",
            message="Published successfully",
            metadata={
                "external_post_id": result.external_post_id,
                "raw": result.raw,
            },
        )

    # Roll up the post-level status from the publication rows after all attempts.
    _roll_up_post_status(post, pubs)

    await db.flush()
    if post.status == "published":
        from app.services import webhook_service

        await webhook_service.fire_event(
            db,
            event="post.published",
            payload={
                "id": str(post.id),
                "title": post.title,
                "brand_id": str(post.brand_id),
                "platforms": [p.provider for p in pubs],
            },
        )
    return post


async def retry_post(db: AsyncSession, post_id: UUID) -> Post | None:
    """Manual retry: reset failed publications to pending so the next sweep runs them."""
    await ensure_publish_schema(db)
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status not in {"failed", "partial", "scheduled", "approved"}:
        raise ValueError(f"Cannot retry a post in status '{post.status}'")
    pubs = await list_publications(db, post_id)
    any_to_retry = False
    for pub in pubs:
        if pub.status in {"failed", "pending"}:
            pub.status = "pending"
            pub.attempts = 0
            pub.next_retry_at = None
            pub.last_attempt_at = None
            pub.remote_status = None
            pub.last_checked_at = None
            pub.permanent_failure = False
            pub.last_error = None
            pub.completed_at = None
            await record_publication_event(
                db,
                pub,
                event_type="manual_retry",
                message="Manual retry requested",
            )
            any_to_retry = True
    if not any_to_retry:
        return post
    post.status = "scheduled"
    post.scheduled_at = _now()
    post.last_error = None
    await db.flush()
    return post


async def _sync_meta_publication(
    db: AsyncSession,
    *,
    publication: PostPublication,
    account: BrandSocialAccount,
) -> None:
    from app.services import meta_service
    from app.services.meta_service import MetaError

    meta = account.metadata_ or {}
    page_token = meta.get("page_token")
    if not page_token:
        publication.remote_status = "auth_error"
        publication.last_error = "Page access token missing — relink the account"
        account.last_error = publication.last_error[:500]
        await record_publication_event(
            db,
            publication,
            event_type="status_sync_failed",
            message=publication.last_error,
            metadata={"reason": "missing_page_token"},
        )
        return

    if not publication.external_post_id:
        publication.remote_status = "unknown"
        publication.last_error = "External post id is missing"
        await record_publication_event(
            db,
            publication,
            event_type="status_sync_failed",
            message=publication.last_error,
        )
        return

    try:
        result = await meta_service.get_published_object(
            db,
            object_id=publication.external_post_id,
            access_token=str(page_token),
        )
    except MetaError as exc:
        if exc.is_auth:
            page_id = str(meta.get("page_id") or account.external_id)
            refreshed = await meta_service.refresh_page_token(db, page_id=page_id)
            if refreshed:
                account.metadata_ = {**meta, "page_token": refreshed}
                result = await meta_service.get_published_object(
                    db,
                    object_id=publication.external_post_id,
                    access_token=refreshed,
                )
            else:
                publication.remote_status = "auth_error"
                publication.last_error = str(exc)[:1000]
                account.last_error = publication.last_error[:500]
                await record_publication_event(
                    db,
                    publication,
                    event_type="status_sync_failed",
                    message=publication.last_error,
                    metadata={"auth": True},
                )
                return
        else:
            publication.remote_status = "unknown"
            publication.last_error = str(exc)[:1000]
            await record_publication_event(
                db,
                publication,
                event_type="status_sync_failed",
                message=publication.last_error,
            )
            return

    publication.remote_status = str(result.get("status") or "live")
    publication.last_error = None
    account.last_error = None
    await record_publication_event(
        db,
        publication,
        event_type="status_synced",
        message="Remote status synced",
        metadata={"remote": dict(result)},
    )


async def sync_post_status(db: AsyncSession, post_id: UUID) -> Post | None:
    """Refresh remote status for already-published platform publications."""
    await ensure_publish_schema(db)
    post = await db.get(Post, post_id)
    if post is None:
        return None

    publications = await list_publications(db, post_id)
    for publication in publications:
        if publication.status != "published":
            continue
        account = await db.get(BrandSocialAccount, publication.social_account_id)
        publication.last_checked_at = _now()
        if account is None or not account.is_active:
            publication.remote_status = "account_missing"
            publication.last_error = (
                "Linked social account no longer exists"
                if account is None
                else "Linked social account is inactive"
            )
            await record_publication_event(
                db,
                publication,
                event_type="status_sync_failed",
                message=publication.last_error,
            )
            continue
        if publication.provider in {"facebook", "instagram"}:
            await _sync_meta_publication(db, publication=publication, account=account)
        elif publication.provider == "telegram":
            publication.remote_status = "sent" if publication.external_post_id else "unknown"
            publication.last_error = None
            await record_publication_event(
                db,
                publication,
                event_type="status_synced",
                message="Telegram delivery id recorded",
                metadata={"message_id": publication.external_post_id},
            )
        else:
            publication.remote_status = "unsupported"
            await record_publication_event(
                db,
                publication,
                event_type="status_sync_skipped",
                message=f"Status sync for {publication.provider} is not supported yet",
            )

    await db.flush()
    return post


async def list_in_range(
    db: AsyncSession,
    *,
    start: datetime,
    end: datetime,
    brand_id: UUID | None = None,
) -> list[Post]:
    """Posts whose scheduled_at OR published_at falls within [start, end)."""
    stmt = (
        select(Post)
        .where(
            ((Post.scheduled_at >= start) & (Post.scheduled_at < end))
            | ((Post.published_at >= start) & (Post.published_at < end))
        )
        .order_by(Post.scheduled_at, Post.published_at)
    )
    if brand_id is not None:
        stmt = stmt.where(Post.brand_id == brand_id)
    return list((await db.execute(stmt)).scalars())


async def stats(db: AsyncSession, brand_id: UUID | None = None) -> dict[str, Any]:
    stmt = select(Post)
    if brand_id is not None:
        stmt = stmt.where(Post.brand_id == brand_id)
    rows = list((await db.execute(stmt)).scalars())
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1
    return {"total": len(rows), "by_status": by_status}


__all__ = [
    "MAX_ATTEMPTS",
    "RETRY_DELAYS_MINUTES",
    "approve",
    "cancel",
    "claim_due_posts",
    "create_post",
    "ensure_publish_schema",
    "get_post",
    "list_in_range",
    "list_posts",
    "list_publication_events",
    "list_publications",
    "publish_now",
    "record_publication_event",
    "reject",
    "reschedule",
    "retry_post",
    "stats",
    "submit_for_review",
    "sync_post_status",
]
