"""Tenant context middleware (pure ASGI to avoid BaseHTTPMiddleware event-loop issues).

Extracts `tenant_schema` from the JWT and attaches it to request scope. The
actual `SET search_path` happens in `get_tenant_db()` per-request.
"""

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.security import InvalidTokenError, decode_token
from app.core.tenancy import validate_schema_name

PUBLIC_PREFIXES = (
    "/api/v1/auth/",
    "/api/v1/health",
    "/api/v1/billing/catalog",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


async def _send_json(send: Send, status_code: int, body: dict[str, str]) -> None:
    payload = json.dumps(body).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": payload})


class TenantContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        if path == "/" or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        auth = headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            await _send_json(send, 401, {"detail": "Missing or malformed Authorization header"})
            return

        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except InvalidTokenError as exc:
            await _send_json(send, 401, {"detail": str(exc)})
            return

        if payload.get("type") != "access":
            await _send_json(send, 401, {"detail": "Token is not an access token"})
            return

        try:
            schema = validate_schema_name(payload.get("tenant_schema", ""))
        except ValueError:
            await _send_json(send, 401, {"detail": "Invalid tenant claim"})
            return

        scope.setdefault("state", {})
        state = scope["state"]
        state["tenant_id"] = payload.get("tenant_id")
        state["tenant_schema"] = schema
        state["user_id"] = payload.get("sub")
        state["role"] = payload.get("role")

        await self.app(scope, receive, send)


__all__ = ["TenantContextMiddleware"]
