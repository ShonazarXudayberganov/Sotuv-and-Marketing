"""Email service with Jinja2 templates and a mock provider for dev/test.

Sprint 5 ships Jinja2 + a logging mock. Real SMTP / SendGrid / Mailgun adapter
is a thin swap once credentials are configured.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol

from jinja2 import Environment, FileSystemLoader, select_autoescape

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
        self.sent.append({"to": to, "subject": subject, "html": html})
        logger.warning("MOCK EMAIL to %s — %s", to, subject)


def get_email_provider() -> EmailProvider:
    """Always returns the mock provider until SMTP/SendGrid creds are wired."""
    return MockEmailProvider()


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
