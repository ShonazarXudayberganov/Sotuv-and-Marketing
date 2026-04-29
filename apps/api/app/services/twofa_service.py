"""TOTP-based two-factor authentication."""

from __future__ import annotations

import base64
import io
import secrets
from datetime import UTC, datetime
from uuid import UUID

import pyotp
import qrcode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.tenant_scoped import TwoFactorSecret


def generate_backup_codes(n: int = 8) -> list[str]:
    return [secrets.token_hex(4).upper() for _ in range(n)]


def make_qr_data_url(otp_uri: str) -> str:
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


async def begin_setup(
    db: AsyncSession, user_id: UUID, account_label: str
) -> tuple[TwoFactorSecret, str, list[str]]:
    """Create or refresh an unverified TOTP secret.

    Returns ``(record, qr_data_url, plain_backup_codes)``.
    """
    existing = (
        (await db.execute(select(TwoFactorSecret).where(TwoFactorSecret.user_id == user_id)))
        .scalars()
        .first()
    )

    secret = pyotp.random_base32()
    backup_codes = generate_backup_codes()
    backup_hashes = [hash_password(code) for code in backup_codes]

    if existing is None:
        record = TwoFactorSecret(
            user_id=user_id,
            secret=secret,
            backup_codes_hash=backup_hashes,
            enabled_at=None,
        )
        db.add(record)
    else:
        existing.secret = secret
        existing.backup_codes_hash = backup_hashes
        existing.enabled_at = None
        record = existing

    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=account_label, issuer_name="NEXUS AI")
    qr_url = make_qr_data_url(otp_uri)
    await db.flush()
    return record, qr_url, backup_codes


async def verify_and_enable(db: AsyncSession, user_id: UUID, code: str) -> bool:
    record = (
        (await db.execute(select(TwoFactorSecret).where(TwoFactorSecret.user_id == user_id)))
        .scalars()
        .first()
    )
    if record is None:
        return False

    totp = pyotp.TOTP(record.secret)
    if totp.verify(code, valid_window=1):
        record.enabled_at = datetime.now(UTC)
        await db.flush()
        return True

    # Try backup codes
    for hashed in record.backup_codes_hash:
        if verify_password(code, hashed):
            # Burn the used code
            record.backup_codes_hash = [h for h in record.backup_codes_hash if h != hashed]
            record.enabled_at = record.enabled_at or datetime.now(UTC)
            await db.flush()
            return True
    return False


async def disable(db: AsyncSession, user_id: UUID) -> None:
    record = (
        (await db.execute(select(TwoFactorSecret).where(TwoFactorSecret.user_id == user_id)))
        .scalars()
        .first()
    )
    if record is not None:
        await db.delete(record)
        await db.flush()
