"""Telegram Bot API client.

Uses the tenant's bot token from ``tenant_integrations`` (provider="telegram_bot").
When no credentials are set OR ``TELEGRAM_MOCK=true``, returns deterministic mock
responses so the UI/tests work without hitting the real API.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.integration_service import get_credentials

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT_SECONDS = 15


class TelegramError(RuntimeError):
    """Raised when the Telegram API returns an error response."""


def _is_mock_mode() -> bool:
    return os.getenv("TELEGRAM_MOCK", "false").lower() in {"1", "true", "yes"}


async def _bot_token(db: AsyncSession) -> str | None:
    creds = await get_credentials(db, "telegram_bot")
    if not creds:
        return None
    token = creds.get("bot_token")
    return str(token) if token else None


async def _call(token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = TELEGRAM_API.format(token=token, method=method)
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
        resp = await http.post(url, json=payload)
        try:
            data = resp.json()
        except ValueError as exc:
            raise TelegramError(f"Non-JSON response (status={resp.status_code})") from exc
    if not data.get("ok"):
        raise TelegramError(data.get("description") or "Telegram API error")
    result = data.get("result")
    if not isinstance(result, dict):
        raise TelegramError("Unexpected Telegram response shape")
    return result


def _mock_get_me() -> dict[str, Any]:
    return {
        "id": 1234567890,
        "is_bot": True,
        "first_name": "Mock NEXUS Bot",
        "username": "nexus_mock_bot",
        "can_join_groups": True,
        "can_read_all_group_messages": False,
        "supports_inline_queries": False,
    }


def _mock_get_chat(chat: str) -> dict[str, Any]:
    handle = chat.lstrip("@")
    return {
        "id": -1001000000000 - (abs(hash(handle)) % 999_999_999),
        "type": "channel",
        "title": f"Mock {handle}",
        "username": handle,
    }


def _mock_send_message(chat_id: int | str, text: str) -> dict[str, Any]:
    return {
        "message_id": abs(hash((chat_id, text))) % 100_000,
        "date": 0,
        "chat": {"id": chat_id, "type": "channel"},
        "text": text,
    }


async def get_me(db: AsyncSession) -> dict[str, Any]:
    """Verify a bot token. Returns the bot's profile (`username`, etc.)."""
    if _is_mock_mode():
        return _mock_get_me()
    token = await _bot_token(db)
    if not token:
        raise TelegramError("Telegram bot token is not configured")
    return await _call(token, "getMe", {})


async def verify_token(token: str) -> dict[str, Any]:
    """Standalone token verification (used during integration connect)."""
    if _is_mock_mode():
        return _mock_get_me()
    return await _call(token, "getMe", {})


async def get_chat(db: AsyncSession, chat: str) -> dict[str, Any]:
    """Resolve a channel/group by @username or numeric chat_id."""
    if _is_mock_mode():
        return _mock_get_chat(chat)
    token = await _bot_token(db)
    if not token:
        raise TelegramError("Telegram bot token is not configured")
    chat_id: str | int = chat
    if isinstance(chat, str) and chat.lstrip("-").isdigit():
        chat_id = int(chat)
    elif isinstance(chat, str) and not chat.startswith("@"):
        chat_id = f"@{chat}"
    return await _call(token, "getChat", {"chat_id": chat_id})


async def send_message(
    db: AsyncSession,
    *,
    chat_id: int | str,
    text: str,
    parse_mode: str | None = "HTML",
    disable_web_page_preview: bool = False,
) -> dict[str, Any]:
    """Send a text message to a Telegram channel/group/user."""
    if _is_mock_mode():
        return _mock_send_message(chat_id, text)
    token = await _bot_token(db)
    if not token:
        raise TelegramError("Telegram bot token is not configured")
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return await _call(token, "sendMessage", payload)


__all__ = [
    "TelegramError",
    "get_chat",
    "get_me",
    "send_message",
    "verify_token",
]
