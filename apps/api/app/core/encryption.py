"""Symmetric encryption helpers for tenant integration credentials.

We use Fernet (AES-128-CBC + HMAC-SHA256). Each tenant's API tokens are
encrypted at rest in the per-tenant `tenant_integrations` table.

The encryption key is process-wide (set via `INTEGRATIONS_ENCRYPTION_KEY`).
Rotating the key requires a re-encryption migration (Sprint 1.2+).
"""

from __future__ import annotations

import base64
import hashlib
import json
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    raw = settings.INTEGRATIONS_ENCRYPTION_KEY.get_secret_value()
    # Accept either a valid Fernet key or any string — derive a valid key from it.
    try:
        return Fernet(raw.encode() if isinstance(raw, str) else raw)
    except (ValueError, TypeError):
        digest = hashlib.sha256(raw.encode()).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_credentials(data: dict[str, Any]) -> str:
    payload = json.dumps(data, separators=(",", ":")).encode()
    return _fernet().encrypt(payload).decode()


def decrypt_credentials(token: str) -> dict[str, Any]:
    try:
        raw = _fernet().decrypt(token.encode())
    except InvalidToken as exc:
        raise ValueError("Cannot decrypt credentials — key mismatch") from exc
    decoded: dict[str, Any] = json.loads(raw)
    return decoded


def mask_secret(value: str, visible: int = 4) -> str:
    """Return the last ``visible`` characters with a leading mask. Used in API responses."""
    if not value:
        return ""
    if len(value) <= visible:
        return "•" * len(value)
    return f"{'•' * 8}{value[-visible:]}"
