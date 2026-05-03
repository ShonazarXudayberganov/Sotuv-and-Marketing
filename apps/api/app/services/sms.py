"""SMS service.

Default behavior in dev/test: log the code instead of calling Eskiz.uz, controlled
by `SMS_MOCK`. Real Eskiz.uz integration kicks in when SMS_MOCK is false AND
ESKIZ_EMAIL/ESKIZ_PASSWORD are populated.
"""

import logging
import secrets
import time
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ESKIZ_BASE_URL = "https://notify.eskiz.uz/api"
ESKIZ_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 25  # tokens expire after ~30 days; refresh early


class SMSProvider(Protocol):
    async def send(self, phone: str, message: str) -> None: ...


class MockSMSProvider:
    """Logs the SMS instead of sending. Used in dev and tests."""

    sent: list[tuple[str, str]] = []

    async def send(self, phone: str, message: str) -> None:
        self.sent.append((phone, message))
        logger.warning("MOCK SMS to %s: %s", phone, message)


class EskizSMSProvider:
    """Eskiz.uz HTTP integration with in-process token caching."""

    _token: str | None = None
    _token_acquired_at: float = 0.0

    async def _login(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            f"{ESKIZ_BASE_URL}/auth/login",
            data={
                "email": settings.ESKIZ_EMAIL,
                "password": settings.ESKIZ_PASSWORD.get_secret_value(),
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        token = resp.json().get("data", {}).get("token")
        if not token:
            raise RuntimeError("Eskiz login: token missing in response")
        EskizSMSProvider._token = str(token)
        EskizSMSProvider._token_acquired_at = time.time()
        return EskizSMSProvider._token

    async def _ensure_token(self, client: httpx.AsyncClient) -> str:
        token = EskizSMSProvider._token
        age = time.time() - EskizSMSProvider._token_acquired_at
        if token is None or age >= ESKIZ_TOKEN_TTL_SECONDS:
            return await self._login(client)
        return token

    async def send(self, phone: str, message: str) -> None:
        digits = "".join(c for c in phone if c.isdigit())
        async with httpx.AsyncClient() as client:
            token = await self._ensure_token(client)
            resp = await client.post(
                f"{ESKIZ_BASE_URL}/message/sms/send",
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "mobile_phone": digits,
                    "message": message,
                    "from": settings.ESKIZ_SENDER,
                },
                timeout=15.0,
            )
            if resp.status_code == 401:
                # token rotated — retry once
                EskizSMSProvider._token = None
                token = await self._ensure_token(client)
                resp = await client.post(
                    f"{ESKIZ_BASE_URL}/message/sms/send",
                    headers={"Authorization": f"Bearer {token}"},
                    data={
                        "mobile_phone": digits,
                        "message": message,
                        "from": settings.ESKIZ_SENDER,
                    },
                    timeout=15.0,
                )
            resp.raise_for_status()


def get_sms_provider() -> SMSProvider:
    if settings.SMS_MOCK or not settings.ESKIZ_EMAIL:
        return MockSMSProvider()
    return EskizSMSProvider()


def generate_verification_code(length: int = 6) -> str:
    """Cryptographically secure numeric code."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))
