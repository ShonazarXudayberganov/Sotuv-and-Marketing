#!/usr/bin/env python3
"""Smoke-check an SMM reviewer environment over HTTP.

No project imports; uses stdlib only so it can run on any machine that has
Python 3. Validates the public web/API surface after staging deploy.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-base-url", required=True, help="Example: https://staging.nexusai.uz")
    parser.add_argument(
        "--api-base-url",
        required=True,
        help="Example: https://api-staging.nexus-ai.uz or https://host/api/v1",
    )
    parser.add_argument("--email", required=True, help="Reviewer demo login email")
    parser.add_argument("--password", required=True, help="Reviewer demo login password")
    parser.add_argument("--require-meta-connected", action="store_true")
    parser.add_argument("--require-meta-oauth", action="store_true")
    parser.add_argument("--require-content-plan", action="store_true")
    return parser.parse_args()


def _trim(url: str) -> str:
    return url.rstrip("/")


def _api_v1_base(api_base_url: str) -> str:
    base = _trim(api_base_url)
    if base.endswith("/api/v1"):
        return base
    return f"{base}/api/v1"


def _http_json(
    method: str,
    url: str,
    *,
    payload: dict[str, object] | None = None,
    token: str | None = None,
) -> tuple[int, dict[str, object]]:
    headers = {"Accept": "application/json"}
    data: bytes | None = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        return exc.code, parsed


def _http_status(url: str) -> int:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status


def _fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    args = parse_args()
    web_base = _trim(args.web_base_url)
    api_base = _trim(args.api_base_url)
    api_v1 = _api_v1_base(api_base)

    print(f"web_base={web_base}")
    print(f"api_base={api_base}")
    print(f"api_v1={api_v1}")

    try:
        web_login = _http_status(f"{web_base}/login")
        web_callback = _http_status(f"{web_base}/settings/integrations/meta/callback")
    except Exception as exc:  # noqa: BLE001
        return _fail(f"web endpoints unreachable: {exc}")

    print(f"web_login_status={web_login}")
    print(f"web_callback_status={web_callback}")
    if web_login != 200 or web_callback != 200:
        return _fail("web reviewer routes are not healthy")

    api_health_url = f"{api_base}/health" if not api_base.endswith("/api/v1") else f"{api_base[:-7]}/health"
    try:
        health_status, health = _http_json("GET", api_health_url)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"api health unreachable: {exc}")

    print(f"api_health_status={health_status}")
    print(f"api_health={json.dumps(health, ensure_ascii=False)}")
    if health_status != 200:
        return _fail("api /health is not healthy")

    login_status, auth = _http_json(
        "POST",
        f"{api_v1}/auth/login",
        payload={"email_or_phone": args.email, "password": args.password},
    )
    print(f"login_status={login_status}")
    if login_status != 200:
        return _fail(f"login failed: {json.dumps(auth, ensure_ascii=False)}")

    token = str(auth.get("access_token") or "")
    if not token:
        return _fail("login returned no access_token")

    integrations_status, integrations = _http_json(
        "GET",
        f"{api_v1}/integrations",
        token=token,
    )
    brands_status, brands = _http_json("GET", f"{api_v1}/brands", token=token)
    plan_status, plan_items = _http_json("GET", f"{api_v1}/content-plan?limit=5", token=token)

    if integrations_status != 200:
        return _fail(f"/integrations failed: {json.dumps(integrations, ensure_ascii=False)}")
    if brands_status != 200:
        return _fail(f"/brands failed: {json.dumps(brands, ensure_ascii=False)}")
    if plan_status != 200:
        return _fail(f"/content-plan failed: {json.dumps(plan_items, ensure_ascii=False)}")

    meta = None
    if isinstance(integrations, list):
        meta = next((row for row in integrations if row.get("provider") == "meta_app"), None)
    if meta is None:
        return _fail("meta_app integration row not found")

    print(f"meta_connected={meta.get('connected')}")
    print(f"meta_oauth_connected={meta.get('oauth_connected')}")
    print(f"meta_status_hint={meta.get('status_hint')}")
    print(f"brands_count={len(brands) if isinstance(brands, list) else 'n/a'}")
    print(f"content_plan_count={len(plan_items) if isinstance(plan_items, list) else 'n/a'}")

    if args.require_meta_connected and not meta.get("connected"):
        return _fail("meta_app is not configured")
    if args.require_meta_oauth and not meta.get("oauth_connected"):
        return _fail("meta_app OAuth is not completed")
    if args.require_content_plan and (not isinstance(plan_items, list) or not plan_items):
        return _fail("content plan reviewer seed is empty")

    print("OK: reviewer readiness checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
