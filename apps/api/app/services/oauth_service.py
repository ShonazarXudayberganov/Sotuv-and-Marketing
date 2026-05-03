"""Google + Telegram OAuth verification.

Both verifiers gracefully fall back to a mock-decode mode controlled by
`OAUTH_MOCK` so dev/test/E2E flows work without real provider credentials.
In mock mode the caller can submit a token of the form
`mock:<email>:<full_name>` and we trust it.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any
from urllib.parse import unquote

from fastapi import HTTPException, status

from app.core.config import settings


class OAuthIdentity:
    def __init__(self, *, provider: str, subject: str, email: str, full_name: str | None) -> None:
        self.provider = provider
        self.subject = subject
        self.email = email
        self.full_name = full_name


def _mock_decode(token: str) -> tuple[str, str | None]:
    """Accept `mock:email[:full_name]` for offline E2E."""
    parts = token.split(":", 2)
    if len(parts) < 2 or parts[0] != "mock":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mock token")
    email = parts[1]
    name = parts[2] if len(parts) == 3 else None
    return email, name


async def verify_google(id_token: str) -> OAuthIdentity:
    """Verify a Google ID token. Falls back to mock decoding when OAUTH_MOCK=true
    or GOOGLE_CLIENT_ID is unset."""
    if settings.OAUTH_MOCK or not settings.GOOGLE_CLIENT_ID:
        email, name = _mock_decode(id_token)
        return OAuthIdentity(
            provider="google",
            subject=f"mock|{email}",
            email=email,
            full_name=name,
        )

    # Real verification — uses Google's tokeninfo endpoint to avoid the
    # google-auth dependency on the hot path. Suitable for low-volume server-
    # side verification.
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
            timeout=15.0,
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Google ID token"
        )
    data = resp.json()
    if data.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token audience mismatch"
        )
    if not data.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email not verified by Google"
        )
    return OAuthIdentity(
        provider="google",
        subject=str(data["sub"]),
        email=str(data["email"]),
        full_name=data.get("name"),
    )


async def verify_telegram(payload: dict[str, Any]) -> OAuthIdentity:
    """Verify a Telegram Login Widget callback (https://core.telegram.org/widgets/login)."""
    if settings.OAUTH_MOCK or not settings.TELEGRAM_BOT_TOKEN.get_secret_value():
        token = str(payload.get("mock_token") or "")
        email, name = _mock_decode(token)
        return OAuthIdentity(
            provider="telegram",
            subject=f"mock|{email}",
            email=email,
            full_name=name,
        )

    received_hash = payload.get("hash")
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram hash missing")

    bot_token = settings.TELEGRAM_BOT_TOKEN.get_secret_value()
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    data_check = "\n".join(
        f"{k}={unquote(str(v))}" for k, v in sorted(payload.items()) if k != "hash"
    )
    expected = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, str(received_hash)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram hash mismatch"
        )

    tg_id = str(payload.get("id", ""))
    username = payload.get("username")
    first_name = payload.get("first_name") or ""
    last_name = payload.get("last_name") or ""
    full_name = f"{first_name} {last_name}".strip() or None
    # Telegram does not expose email; we synthesize a stable address so we can
    # reuse the existing email-keyed user table. Owners can update later.
    synth_email = f"tg{tg_id}@telegram.nexusai.uz"
    if username:
        synth_email = f"{username}@telegram.nexusai.uz"
    return OAuthIdentity(
        provider="telegram",
        subject=tg_id,
        email=synth_email,
        full_name=full_name,
    )
