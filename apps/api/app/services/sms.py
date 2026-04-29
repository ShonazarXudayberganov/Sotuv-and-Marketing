"""SMS service.

Default behavior in dev/test: log the code instead of calling Eskiz.uz, controlled
by `SMS_MOCK`. Eskiz integration goes here when credentials are available.
"""

import logging
import secrets
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSProvider(Protocol):
    async def send(self, phone: str, message: str) -> None: ...


class MockSMSProvider:
    """Logs the SMS instead of sending. Used in dev and tests."""

    sent: list[tuple[str, str]] = []

    async def send(self, phone: str, message: str) -> None:
        self.sent.append((phone, message))
        logger.warning("MOCK SMS to %s: %s", phone, message)


class EskizSMSProvider:
    """Eskiz.uz integration — wired in Sprint 1 when credentials are ready."""

    async def send(self, phone: str, message: str) -> None:
        # TODO(sprint-1): implement Eskiz.uz API call once ESKIZ_EMAIL/PASSWORD are set
        raise NotImplementedError("Eskiz integration not yet wired — set SMS_MOCK=true")


def get_sms_provider() -> SMSProvider:
    if settings.SMS_MOCK or not settings.ESKIZ_EMAIL:
        return MockSMSProvider()
    return EskizSMSProvider()


def generate_verification_code(length: int = 6) -> str:
    """Cryptographically secure numeric code."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))
