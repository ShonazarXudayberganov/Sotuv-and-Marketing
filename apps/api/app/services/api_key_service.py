"""API key generation/verification."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.tenant_scoped import ApiKey

PREFIX = "nxa_"  # nexus api


def generate_plaintext() -> tuple[str, str]:
    """Returns (full_plaintext, prefix-display)."""
    body = secrets.token_urlsafe(32)
    plain = f"{PREFIX}{body}"
    return plain, plain[:12]


async def create(
    db: AsyncSession,
    *,
    user_id: UUID,
    name: str,
    scopes: list[str],
    rate_limit_per_minute: int,
    expires_in_days: int | None = None,
) -> tuple[ApiKey, str]:
    plain, prefix = generate_plaintext()
    expires_at: datetime | None = None
    if expires_in_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

    key = ApiKey(
        name=name,
        key_prefix=prefix,
        key_hash=hash_password(plain),
        created_by=user_id,
        scopes=list(scopes),
        rate_limit_per_minute=rate_limit_per_minute,
        expires_at=expires_at,
    )
    db.add(key)
    await db.flush()
    return key, plain
