"""
Launch-57 anonymous public surface — per-route cost guards + AV-24 leak scan.

Applies only to cookie-less allowlisted public routes. Does not expand allowlist.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse, Response

from anonymous_route_foundation import (
    AUTH_FLOW_EXACT,
    AUTH_FLOW_PREFIXES,
    INFRASTRUCTURE_EXACT,
    INFRASTRUCTURE_PREFIXES,
    LAUNCH57_PUBLIC_API_EXACT,
    LAUNCH57_PUBLIC_API_PREFIXES,
    PATH_ORACLE_ACCURACY,
    PRIVATE_DATA_PATTERNS,
    PUBLIC_API_EXACT,
    PUBLIC_HTML_EXACT,
    is_anonymous_route_allowed,
    request_has_authentication_signal,
)

GUARD_VERSION = "launch57-anonymous-public-cost-guards-1.0.0"

# AV-24 — forbidden private values in anonymous public responses.
_SENSITIVE_VALUE_KEYS = frozenset(
    {
        "user_id",
        "email",
        "username",
        "password",
        "password_hash",
        "api_key",
        "bd_token",
        "session_token",
        "session_id",
        "wallet_address",
        "wallet_addresses",
        "holdings",
        "portfolio",
        "watchlist",
        "watchlists",
        "decision_history",
        "personal_decision_history",
        "discipline_mirror",
        "telegram_chat_id",
        "billing_customer_id",
        "subscription_id",
        "payment_method_reference",
        "account_settings",
        "mfa_secret",
        "recovery_codes",
    }
)


@dataclass(frozen=True)
class PublicRouteCostPolicy:
    path_pattern: str
    bucket: str
    rate_limit: int
    rate_window_sec: int
    max_response_bytes: int
    timeout_sec: float
    upstream_budget: int = 1


def _bucket_for_path(path: str) -> str:
    if path in INFRASTRUCTURE_EXACT or any(path.startswith(p) for p in INFRASTRUCTURE_PREFIXES):
        return "infrastructure"
    if path in AUTH_FLOW_EXACT or any(path.startswith(p) for p in AUTH_FLOW_PREFIXES):
        return "auth_flow"
    if path in PUBLIC_HTML_EXACT:
        return "public_html"
    if path in PUBLIC_API_EXACT or path in LAUNCH57_PUBLIC_API_EXACT:
        return "public_api"
    if any(path.startswith(p) for p in LAUNCH57_PUBLIC_API_PREFIXES):
        return "public_api"
    return "public"


def _default_policy_for_bucket(bucket: str, path: str) -> PublicRouteCostPolicy:
    if bucket == "infrastructure":
        return PublicRouteCostPolicy(path, bucket, 180, 60, 1_048_576, 5.0, 0)
    if bucket == "auth_flow":
        return PublicRouteCostPolicy(path, bucket, 40, 60, 131_072, 10.0, 0)
    if bucket == "public_html":
        return PublicRouteCostPolicy(path, bucket, 90, 60, 2_097_152, 15.0, 0)
    if path == "/api/launch57/real-time-prices":
        return PublicRouteCostPolicy(path, bucket, 45, 60, 262_144, 8.0, 1)
    if path.startswith("/api/launch57/"):
        return PublicRouteCostPolicy(path, bucket, 60, 60, 393_216, 12.0, 1)
    if path == "/api/status":
        return PublicRouteCostPolicy(path, bucket, 120, 60, 131_072, 5.0, 0)
    return PublicRouteCostPolicy(path, bucket, 60, 60, 262_144, 10.0, 1)


def _exact_policy_overrides() -> dict[str, PublicRouteCostPolicy]:
    overrides: dict[str, PublicRouteCostPolicy] = {}
    for path in sorted(
        INFRASTRUCTURE_EXACT
        | AUTH_FLOW_EXACT
        | PUBLIC_HTML_EXACT
        | PUBLIC_API_EXACT
        | LAUNCH57_PUBLIC_API_EXACT
    ):
        bucket = _bucket_for_path(path)
        overrides[path] = _default_policy_for_bucket(bucket, path)
    return overrides


PUBLIC_ROUTE_COST_POLICIES: dict[str, PublicRouteCostPolicy] = _exact_policy_overrides()

PREFIX_ROUTE_COST_POLICIES: tuple[tuple[str, PublicRouteCostPolicy], ...] = (
    (
        "/static/",
        PublicRouteCostPolicy("/static/*", "infrastructure", 300, 60, 5_242_880, 10.0, 0),
    ),
    (
        "/health/",
        PublicRouteCostPolicy("/health/*", "infrastructure", 180, 60, 65_536, 3.0, 0),
    ),
    (
        "/api/auth/oauth/",
        PublicRouteCostPolicy("/api/auth/oauth/*", "auth_flow", 40, 60, 131_072, 10.0, 0),
    ),
    (
        "/api/launch57/capability-library/",
        PublicRouteCostPolicy(
            "/api/launch57/capability-library/*",
            "public_api",
            60,
            60,
            393_216,
            12.0,
            1,
        ),
    ),
)


def resolve_public_cost_policy(path: str) -> PublicRouteCostPolicy | None:
    if path in PUBLIC_ROUTE_COST_POLICIES:
        return PUBLIC_ROUTE_COST_POLICIES[path]
    for prefix, policy in PREFIX_ROUTE_COST_POLICIES:
        if path.startswith(prefix):
            return policy
    if is_anonymous_route_allowed("GET", path):
        bucket = _bucket_for_path(path)
        return _default_policy_for_bucket(bucket, path)
    return None


def build_public_route_cost_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, policy in sorted(PUBLIC_ROUTE_COST_POLICIES.items()):
        rows.append(
            {
                "path": path,
                "bucket": policy.bucket,
                "rate_limit": policy.rate_limit,
                "rate_window_sec": policy.rate_window_sec,
                "max_response_bytes": policy.max_response_bytes,
                "timeout_sec": policy.timeout_sec,
                "upstream_budget": policy.upstream_budget,
            }
        )
    for prefix, policy in PREFIX_ROUTE_COST_POLICIES:
        rows.append(
            {
                "path": prefix + "*",
                "bucket": policy.bucket,
                "rate_limit": policy.rate_limit,
                "rate_window_sec": policy.rate_window_sec,
                "max_response_bytes": policy.max_response_bytes,
                "timeout_sec": policy.timeout_sec,
                "upstream_budget": policy.upstream_budget,
            }
        )
    return rows


def _client_key(request: Request) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if request.client and request.client.host:
        return request.client.host
    return "anonymous"


def enforce_public_rate_limit(request: Request, policy: PublicRouteCostPolicy) -> None:
    from viral_capacity import check_rate_limit

    client = _client_key(request)
    path = request.url.path or ""
    check_rate_limit(
        f"{path}:{client}",
        limit=policy.rate_limit,
        window_sec=policy.rate_window_sec,
        prefix="anon_public",
    )


def _is_sensitive_value(key: str, value: Any) -> bool:
    kl = str(key).lower()
    if kl not in _SENSITIVE_VALUE_KEYS:
        return False
    if kl == "email":
        return isinstance(value, str) and "@" in value
    if kl == "username":
        return isinstance(value, str) and value and "@" not in value
    if kl == "password_hash":
        return isinstance(value, str) and len(value) > 40 and value not in {
            "pbkdf2_sha256",
            "bcrypt",
            "argon2",
        }
    if kl in {"portfolio", "holdings", "watchlist", "watchlists", "decision_history", "personal_decision_history", "discipline_mirror", "account_settings", "recovery_codes"}:
        return isinstance(value, (dict, list)) and len(value) > 0
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None and value is not False and value != 0


def _collect_forbidden_keys(payload: Any, prefix: str = "") -> list[str]:
    leaked: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            full = f"{prefix}.{key}" if prefix else str(key)
            if _is_sensitive_value(key, value):
                leaked.append(full)
            leaked.extend(_collect_forbidden_keys(value, full))
    elif isinstance(payload, list):
        for idx, item in enumerate(payload[:50]):
            leaked.extend(_collect_forbidden_keys(item, f"{prefix}[{idx}]"))
    return leaked


def scan_public_response_for_av24_leak(
    *,
    path: str,
    status_code: int,
    body_text: str,
    content_type: str = "",
) -> dict[str, Any]:
    """AV-24 — detect wallet/email/session/personal-history leakage in public responses."""
    if status_code not in {200, 201, 204}:
        return {
            "path": path,
            "status_code": status_code,
            "boundary_ok": True,
            "skipped": True,
            "reason": "non_success_status",
        }

    pattern_hits = [p.pattern for p in PRIVATE_DATA_PATTERNS if p.search(body_text or "")]
    json_key_hits: list[str] = []
    if "json" in (content_type or "").lower():
        try:
            parsed = json.loads(body_text or "{}")
            json_key_hits = _collect_forbidden_keys(parsed)
        except json.JSONDecodeError:
            json_key_hits = []

    leaked = sorted(set(json_key_hits))
    boundary_ok = not pattern_hits and not leaked
    return {
        "path": path,
        "status_code": status_code,
        "boundary_ok": boundary_ok,
        "pattern_hits": pattern_hits,
        "forbidden_keys": leaked,
        "skipped": False,
    }


async def _read_response_body(response: Response) -> tuple[Response, bytes]:
    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    response.body_iterator = None  # type: ignore[attr-defined]
    return response, body


async def cap_public_response_size(response: Response, policy: PublicRouteCostPolicy) -> Response:
    if policy.max_response_bytes <= 0:
        return response
    _, body = await _read_response_body(response)
    if len(body) <= policy.max_response_bytes:
        response.headers["Content-Length"] = str(len(body))
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
    return JSONResponse(
        status_code=413,
        content={
            "error": "response_too_large",
            "message": "Anonymous public response exceeded size cap.",
            "path": policy.path_pattern,
            "max_response_bytes": policy.max_response_bytes,
        },
        headers={"X-Blackdark-Public-Size-Cap": str(policy.max_response_bytes)},
    )


async def apply_public_cost_guards(request: Request, call_next) -> Response:
    path = request.url.path or ""
    policy = resolve_public_cost_policy(path)
    if policy is None:
        return await call_next(request)

    try:
        enforce_public_rate_limit(request, policy)
    except HTTPException as exc:
        return JSONResponse(
            exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail},
            status_code=exc.status_code,
            headers=dict(exc.headers or {}),
        )
    try:
        response = await asyncio.wait_for(call_next(request), timeout=policy.timeout_sec)
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={
                "error": "public_route_timeout",
                "message": "Anonymous public route exceeded timeout budget.",
                "path": path,
                "timeout_sec": policy.timeout_sec,
            },
            headers={"X-Blackdark-Public-Timeout": str(policy.timeout_sec)},
        )
    except HTTPException as exc:
        return JSONResponse(
            exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail},
            status_code=exc.status_code,
            headers=dict(exc.headers or {}),
        )

    capped = await cap_public_response_size(response, policy)
    capped.headers.setdefault("X-Blackdark-Public-Rate-Limit", str(policy.rate_limit))
    capped.headers.setdefault("X-Blackdark-Public-Timeout", str(policy.timeout_sec))
    capped.headers.setdefault("X-Blackdark-Public-Size-Cap", str(policy.max_response_bytes))
    return capped


async def anonymous_public_cost_guard_middleware(request: Request, call_next):
    if request_has_authentication_signal(request):
        return await call_next(request)
    path = request.url.path or ""
    if not is_anonymous_route_allowed(request.method or "GET", path):
        return await call_next(request)
    return await apply_public_cost_guards(request, call_next)


def iter_allowlist_probe_paths() -> list[tuple[str, str, dict[str, str] | None]]:
    """GET paths to probe for AV-24 sweep (method, path, params)."""
    probes: list[tuple[str, str, dict[str, str] | None]] = []
    skip_post_only = {
        "/join-waitlist",
        "/api/legal/ack-terms",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/forgot-password",
        "/api/auth/reset-password",
        "/api/auth/verify-email",
        "/api/auth/resend-verification",
        "/api/auth/forgot-username",
        "/api/auth/mfa/complete",
    }
    for path in sorted(PUBLIC_ROUTE_COST_POLICIES):
        if path in skip_post_only:
            continue
        params = None
        if path.startswith("/api/launch57/"):
            params = {"symbol": "BTC"}
            if path == "/api/launch57/capability-library":
                params = {"q": "oracle"}
        probes.append(("GET", path, params))
    for prefix, _ in PREFIX_ROUTE_COST_POLICIES:
        if prefix == "/static/":
            probes.append(("GET", "/static/css/trust-os.css", None))
        elif prefix == "/health/":
            probes.append(("GET", "/health/live", None))
        elif prefix == "/api/launch57/capability-library/":
            probes.append(("GET", "/api/launch57/capability-library/search", {"q": "trust"}))
    return probes


def sweep_allowlist_av24(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(results)
    failures = [r for r in rows if not r.get("boundary_ok") and not r.get("skipped")]
    return {
        "scanned": len(rows),
        "failures": failures,
        "boundary_ok": len(failures) == 0,
    }
