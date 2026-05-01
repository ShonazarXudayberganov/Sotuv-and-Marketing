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

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smm import (
    Brand,
    BrandSocialAccount,
    ContentDraft,
    Post,
    PostPublication,
)
from app.services import publisher_service
from app.services.publisher_service import PublishError, UnsupportedProviderError

# Retry plan (cumulative): attempt 0 + 3 retries.
RETRY_DELAYS_MINUTES = (5, 30, 60)
MAX_ATTEMPTS = len(RETRY_DELAYS_MINUTES) + 1  # 4 total attempts


def _now() -> datetime:
    return datetime.now(UTC)


def _next_retry_at(attempts: int) -> datetime | None:
    """attempts=1 -> +5min; attempts=2 -> +30min; attempts=3 -> +60min; else None."""
    if attempts < 1 or attempts > len(RETRY_DELAYS_MINUTES):
        return None
    return _now() + timedelta(minutes=RETRY_DELAYS_MINUTES[attempts - 1])


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
    stmt = (
        select(PostPublication)
        .where(PostPublication.post_id == post_id)
        .order_by(PostPublication.created_at)
    )
    return list((await db.execute(stmt)).scalars())


async def cancel(db: AsyncSession, post_id: UUID) -> Post | None:
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status not in {"draft", "scheduled"}:
        raise ValueError(f"Cannot cancel a post in status '{post.status}'")
    post.status = "cancelled"
    await db.flush()
    return post


async def reschedule(
    db: AsyncSession, post_id: UUID, scheduled_at: datetime | None
) -> Post | None:
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status not in {"draft", "scheduled"}:
        raise ValueError(f"Cannot reschedule a post in status '{post.status}'")
    post.scheduled_at = scheduled_at
    post.status = "scheduled" if scheduled_at is not None else "draft"
    await db.flush()
    return post


async def claim_due_posts(db: AsyncSession, limit: int = 25) -> list[Post]:
    """Atomically flip due posts to 'publishing' so only one worker runs them."""
    now = _now()
    stmt = (
        update(Post)
        .where(Post.status == "scheduled", Post.scheduled_at <= now)
        .values(status="publishing")
        .returning(Post.id)
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    ids = [row[0] for row in result.fetchall()[:limit]]
    if not ids:
        return []
    fetched = await db.execute(select(Post).where(Post.id.in_(ids)))
    return list(fetched.scalars())


async def publish_now(db: AsyncSession, post: Post) -> Post:
    """Run all pending publications for a post and persist outcomes."""
    post.status = "publishing"
    await db.flush()

    pubs = await list_publications(db, post.id)
    any_failed = False
    any_pending_retry = False

    for pub in pubs:
        if pub.status in {"published", "skipped"}:
            continue
        account = await db.get(BrandSocialAccount, pub.social_account_id)
        if account is None:
            pub.status = "failed"
            pub.last_error = "Linked social account no longer exists"
            pub.completed_at = _now()
            any_failed = True
            continue

        pub.attempts += 1
        try:
            result = await publisher_service.publish(db, account=account, post=post)
        except UnsupportedProviderError as exc:
            # Permanent failure — no retries.
            pub.last_error = str(exc)[:1000]
            pub.status = "failed"
            pub.completed_at = _now()
            pub.next_retry_at = None
            any_failed = True
            continue
        except PublishError as exc:
            pub.last_error = str(exc)[:1000]
            if pub.attempts >= MAX_ATTEMPTS:
                pub.status = "failed"
                pub.completed_at = _now()
                pub.next_retry_at = None
                any_failed = True
            else:
                pub.status = "pending"
                pub.next_retry_at = _next_retry_at(pub.attempts)
                any_pending_retry = True
            continue

        pub.status = "published"
        pub.external_post_id = result.external_post_id
        pub.last_error = None
        pub.next_retry_at = None
        pub.completed_at = _now()

    # Roll up the post-level status from the publications.
    if any_pending_retry and not any_failed:
        post.status = "scheduled"
        # bump scheduled_at to the earliest pending retry so the worker re-sweeps
        retry_times = [
            p.next_retry_at for p in pubs if p.next_retry_at is not None
        ]
        if retry_times:
            post.scheduled_at = min(retry_times)
        post.last_error = None
    elif any_failed and not all(p.status == "failed" for p in pubs):
        post.status = "partial"
        post.last_error = "Some platforms failed; others succeeded"
        post.published_at = _now()
    elif any_failed:
        post.status = "failed"
        post.last_error = "All platforms failed after maximum retries"
    else:
        post.status = "published"
        post.published_at = _now()
        post.last_error = None

    await db.flush()
    return post


async def retry_post(db: AsyncSession, post_id: UUID) -> Post | None:
    """Manual retry: reset failed publications to pending so the next sweep runs them."""
    post = await db.get(Post, post_id)
    if post is None:
        return None
    if post.status not in {"failed", "partial", "scheduled"}:
        raise ValueError(f"Cannot retry a post in status '{post.status}'")
    pubs = await list_publications(db, post_id)
    any_to_retry = False
    for pub in pubs:
        if pub.status in {"failed", "pending"}:
            pub.status = "pending"
            pub.next_retry_at = None
            pub.last_error = None
            any_to_retry = True
    if not any_to_retry:
        return post
    post.status = "scheduled"
    post.scheduled_at = _now()
    post.last_error = None
    await db.flush()
    return post


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
    "cancel",
    "claim_due_posts",
    "create_post",
    "get_post",
    "list_posts",
    "list_publications",
    "publish_now",
    "reschedule",
    "retry_post",
    "stats",
]
