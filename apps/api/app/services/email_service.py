"""Email service with Jinja2 templates and a mock provider for dev/test.

Sprint 5 ships Jinja2 + a logging mock. Real SMTP adapter (SMTPEmailProvider) is
selected automatically when EMAIL_MOCK is false and SMTP_HOST is configured.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Protocol

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "ai" / "prompts" / "_emails"
# Templates are colocated with email-related text to keep prompts/templates near.

_FALLBACK_DIR = Path(__file__).resolve().parents[2] / "templates" / "emails"


def _env() -> Environment:
    search_dirs = [str(d) for d in (_TEMPLATES_DIR, _FALLBACK_DIR) if d.exists()]
    return Environment(
        loader=FileSystemLoader(search_dirs or [str(_FALLBACK_DIR)]),
        autoescape=select_autoescape(["html", "xml"]),
        keep_trailing_newline=True,
    )


def render_template(name: str, **context: Any) -> str:
    return _env().get_template(name).render(**context)


class EmailProvider(Protocol):
    async def send(self, *, to: str, subject: str, html: str, text: str | None = None) -> None: ...


class MockEmailProvider:
    sent: list[dict[str, str]] = []

    async def send(self, *, to: str, subject: str, html: str, text: str | None = None) -> None:
        self.sent.append({"to": to, "subject": subject, "html": html, "text": text or ""})
        logger.warning("MOCK EMAIL to %s — %s", to, subject)


class SMTPEmailProvider:
    """Synchronous smtplib wrapped in a thread for async compatibility."""

    def _send_sync(self, *, to: str, subject: str, html: str, text: str | None) -> None:
        msg = EmailMessage()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(text or "")
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
            smtp.ehlo()
            if settings.SMTP_TLS:
                smtp.starttls()
                smtp.ehlo()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
            smtp.send_message(msg)

    async def send(self, *, to: str, subject: str, html: str, text: str | None = None) -> None:
        await asyncio.to_thread(self._send_sync, to=to, subject=subject, html=html, text=text)


def get_email_provider() -> EmailProvider:
    if settings.EMAIL_MOCK or not settings.SMTP_HOST:
        return MockEmailProvider()
    return SMTPEmailProvider()


async def send_invoice_email(*, to: str, invoice_number: str, amount: int, due_at: str) -> None:
    provider = get_email_provider()
    html = (
        f"<h2>Hisob faktura — {invoice_number}</h2>"
        f"<p>To'lov miqdori: <b>{amount:,} so'm</b></p>"
        f"<p>To'lov muddati: {due_at}</p>"
        f"<p>Bank o'tkazmasi orqali to'lang. Reqvizitlar invoice PDF faylida.</p>"
    )
    await provider.send(
        to=to,
        subject=f"NEXUS AI — Invoice {invoice_number}",
        html=html,
    )
