"""Integration credentials lifecycle.

Each integration is keyed by ``provider`` (e.g. ``anthropic``, ``openai``,
``telegram_bot``, ``meta_app``, ``google_oauth``, ``eskiz_sms``, ``sendgrid``,
``instagram_business``, ``facebook_page``, ``youtube_channel``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_credentials, encrypt_credentials, mask_secret
from app.models.smm import TenantIntegration

# Provider catalog — single source of truth for the UI.
# `secret_fields` are stored encrypted; `display_field` is shown unmasked.
PROVIDERS: dict[str, dict[str, Any]] = {
    "anthropic": {
        "label": "Anthropic (Claude)",
        "category": "ai",
        "description": "AI kontent generatsiya, suhbat, biznes maslahat",
        "secret_fields": ["api_key"],
        "display_field": None,
        "docs_url": "https://console.anthropic.com",
    },
    "openai": {
        "label": "OpenAI (GPT-4o + Embeddings)",
        "category": "ai",
        "description": "Backup AI + embeddinglar (RAG uchun)",
        "secret_fields": ["api_key"],
        "display_field": None,
        "docs_url": "https://platform.openai.com",
    },
    "telegram_bot": {
        "label": "Telegram Bot",
        "category": "social",
        "description": "Bot orqali post va auto-javob",
        "secret_fields": ["bot_token"],
        "display_field": "bot_username",
        "docs_url": "https://t.me/BotFather",
    },
    "meta_app": {
        "label": "Meta (Facebook + Instagram)",
        "category": "social",
        "description": "Instagram Business va Facebook Page postlash",
        "secret_fields": ["app_id", "app_secret", "page_access_token"],
        "display_field": "page_name",
        "docs_url": "https://developers.facebook.com",
    },
    "youtube": {
        "label": "YouTube Data API",
        "category": "social",
        "description": "Video metadata, comments, analytics",
        "secret_fields": ["api_key", "oauth_refresh_token"],
        "display_field": "channel_name",
        "docs_url": "https://console.cloud.google.com",
    },
    "google_oauth": {
        "label": "Google OAuth (Sign-in)",
        "category": "auth",
        "description": "Foydalanuvchilar Google orqali kirish",
        "secret_fields": ["client_id", "client_secret"],
        "display_field": None,
        "docs_url": "https://console.cloud.google.com/apis/credentials",
    },
    "eskiz_sms": {
        "label": "Eskiz.uz (SMS)",
        "category": "messaging",
        "description": "SMS tasdiqlash va xabarlar",
        "secret_fields": ["email", "password", "sender"],
        "display_field": "sender",
        "docs_url": "https://eskiz.uz",
    },
    "sendgrid": {
        "label": "SendGrid (Email)",
        "category": "messaging",
        "description": "Tranzaksiya emaillari (invoice, taklif, ogohlantirish)",
        "secret_fields": ["api_key", "from_email"],
        "display_field": "from_email",
        "docs_url": "https://app.sendgrid.com",
    },
    "amocrm": {
        "label": "AmoCRM",
        "category": "crm",
        "description": "Mijozlar va bitimlar dvustoronniy sinxronizatsiya",
        "secret_fields": ["subdomain", "client_id", "client_secret", "access_token"],
        "display_field": "subdomain",
        "docs_url": "https://www.amocrm.ru/developers/content/oauth/step-by-step",
    },
    "bitrix24": {
        "label": "Bitrix24",
        "category": "crm",
        "description": "Bitrix24 lead va deal sinxronizatsiya",
        "secret_fields": ["portal_url", "webhook_url", "client_id", "client_secret"],
        "display_field": "portal_url",
        "docs_url": "https://training.bitrix24.com/rest_help/",
    },
    "onec": {
        "label": "1C (Buxgalteriya)",
        "category": "erp",
        "description": "1C orqali invoice va to'lov sinxronizatsiya",
        "secret_fields": ["base_url", "username", "password"],
        "display_field": "base_url",
        "docs_url": "https://its.1c.ru/",
    },
    "google_sheets": {
        "label": "Google Sheets",
        "category": "data",
        "description": "Mijozlar/bitimlar Google Sheets'ga avtomatik eksport",
        "secret_fields": ["service_account_json"],
        "display_field": "spreadsheet_id",
        "docs_url": "https://developers.google.com/sheets/api",
    },
    "webhook_outgoing": {
        "label": "Generic Webhook (Outbound)",
        "category": "data",
        "description": "Tashqi tizimlarga voqea xabarlarini POST qilish",
        "secret_fields": ["url", "secret"],
        "display_field": "url",
        "docs_url": None,
    },
    "zapier": {
        "label": "Zapier",
        "category": "data",
        "description": "5000+ ilovaga ulanish (Zap orqali)",
        "secret_fields": ["webhook_url"],
        "display_field": "webhook_url",
        "docs_url": "https://zapier.com",
    },
}


class UnknownProviderError(ValueError):
    pass


async def upsert(
    db: AsyncSession,
    *,
    provider: str,
    credentials: dict[str, Any],
    user_id: UUID,
    label: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> TenantIntegration:
    if provider not in PROVIDERS:
        raise UnknownProviderError(f"Unknown provider: {provider}")

    spec = PROVIDERS[provider]
    missing = [f for f in spec["secret_fields"] if not credentials.get(f)]
    if missing:
        raise ValueError(f"Required fields missing: {', '.join(missing)}")

    existing = (
        (await db.execute(select(TenantIntegration).where(TenantIntegration.provider == provider)))
        .scalars()
        .first()
    )

    encrypted = encrypt_credentials(credentials)

    if existing is not None:
        existing.credentials_encrypted = encrypted
        existing.label = label or existing.label
        existing.metadata_ = metadata
        existing.is_active = True
        existing.last_error = None
        rec = existing
    else:
        rec = TenantIntegration(
            provider=provider,
            label=label,
            credentials_encrypted=encrypted,
            metadata_=metadata,
            created_by=user_id,
            is_active=True,
        )
        db.add(rec)
    await db.flush()
    return rec


async def get_credentials(db: AsyncSession, provider: str) -> dict[str, Any] | None:
    row = (
        (await db.execute(select(TenantIntegration).where(TenantIntegration.provider == provider)))
        .scalars()
        .first()
    )
    if row is None or not row.is_active:
        return None
    return decrypt_credentials(row.credentials_encrypted)


async def list_with_status(db: AsyncSession) -> list[dict[str, Any]]:
    """Return one row per known provider — connected or not — for the UI."""
    rows = (await db.execute(select(TenantIntegration))).scalars()
    by_provider = {r.provider: r for r in rows}

    out: list[dict[str, Any]] = []
    for key, spec in PROVIDERS.items():
        rec = by_provider.get(key)
        connected = rec is not None and rec.is_active
        public_display: str | None = None
        masked: dict[str, str] = {}
        if connected and rec is not None:
            try:
                creds = decrypt_credentials(rec.credentials_encrypted)
            except ValueError:
                creds = {}
            for f in spec["secret_fields"]:
                masked[f] = mask_secret(str(creds.get(f, "")))
            display_key = spec.get("display_field")
            if display_key:
                public_display = creds.get(display_key)

        out.append(
            {
                "provider": key,
                "label": spec["label"],
                "category": spec["category"],
                "description": spec["description"],
                "secret_fields": spec["secret_fields"],
                "display_field": spec.get("display_field"),
                "docs_url": spec.get("docs_url"),
                "connected": connected,
                "is_active": rec.is_active if rec else False,
                "label_custom": rec.label if rec else None,
                "display_value": public_display,
                "masked_values": masked,
                "last_verified_at": rec.last_verified_at.isoformat()
                if rec and rec.last_verified_at
                else None,
                "last_error": rec.last_error if rec else None,
                "updated_at": rec.updated_at.isoformat() if rec else None,
            }
        )
    return out


async def disconnect(db: AsyncSession, provider: str) -> bool:
    row = (
        (await db.execute(select(TenantIntegration).where(TenantIntegration.provider == provider)))
        .scalars()
        .first()
    )
    if row is None:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def mark_verified(
    db: AsyncSession, provider: str, *, ok: bool, error: str | None = None
) -> None:
    row = (
        (await db.execute(select(TenantIntegration).where(TenantIntegration.provider == provider)))
        .scalars()
        .first()
    )
    if row is None:
        return
    row.last_verified_at = datetime.now(UTC) if ok else row.last_verified_at
    row.last_error = None if ok else (error or "Verification failed")
    await db.flush()
