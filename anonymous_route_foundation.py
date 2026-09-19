"""
BLACKDARK — P0 Anonymous Security & Route Foundation (AV-01..AV-03).

Canonical owner for:
- Product auth states (ANONYMOUS + tier states)
- PRIVATE_BY_DEFAULT enforcement
- ANONYMOUS_ROUTE_ALLOWLIST
- Route inventory + classification
- Server-side anonymous boundary enforcement
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Iterable, Mapping

from fastapi import Request
from starlette.responses import JSONResponse, Response

GOVERNING_SPEC = "docs/BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL.md"
CONTRACT_VERSION = "anonymous_route_foundation.p0.1.0"
PRIVATE_BY_DEFAULT = True

# Re-exported for public_api_docs compatibility (single allowlist owner).
PATH_API_TRUST_OS = "/api/trust-os"
PATH_ORACLE_ACCURACY = "/oracle-accuracy"


class ProductAuthState(str, Enum):
    ANONYMOUS = "ANONYMOUS"
    FREE_ACCOUNT = "FREE_ACCOUNT"
    PAID_INDIVIDUAL = "PAID_INDIVIDUAL"
    INSTITUTIONAL = "INSTITUTIONAL"


class RouteAccessClass(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"
    INTERNAL = "internal"


class RouteDataClass(str, Enum):
    PUBLIC_INTELLIGENCE = "public_intelligence"
    INFRASTRUCTURE = "infrastructure"
    AUTH_FLOW = "auth_flow"
    USER_PRIVATE = "user_private"
    ADMIN_SENSITIVE = "admin_sensitive"
    INTERNAL_CALLBACK = "internal_callback"
    MIXED = "mixed"


# --- Infrastructure (anonymous visitor + probes) ---
INFRASTRUCTURE_EXACT: frozenset[str] = frozenset(
    {
        "/",
        "/favicon.ico",
        "/robots.txt",
        "/sitemap.xml",
        "/manifest.json",
        "/health",
        "/health/live",
        "/health/ready",
        "/health/viral",
        "/metrics",
    }
)

INFRASTRUCTURE_PREFIXES: tuple[str, ...] = (
    "/static/",
)

# --- Auth / conversion flows (anonymous may call before session exists) ---
AUTH_FLOW_EXACT: frozenset[str] = frozenset(
    {
        "/login",
        "/register",
        "/reset-password",
        "/verify-email",
        "/api/legal/ack-terms",
        "/api/auth/identity",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/forgot-password",
        "/api/auth/reset-password",
        "/api/auth/verify-email",
        "/api/auth/resend-verification",
        "/api/auth/forgot-username",
        "/api/auth/mfa/complete",
        "/api/auth/oauth/status",
        "/api/i18n/locales",
        "/api/i18n/catalog",
    }
)

AUTH_FLOW_PREFIXES: tuple[str, ...] = (
    "/api/auth/oauth/",
)

# --- Public HTML / marketing / evidence surfaces ---
PUBLIC_HTML_EXACT: frozenset[str] = frozenset(
    {
        "/about",
        "/how-it-works",
        "/faq",
        "/status",
        "/legal",
        "/cookies",
        "/disclaimer",
        "/compliance",
        "/contact",
        "/docs",
        "/docs/public",
        "/capabilities",
        "/data-room",
        "/landing",
        "/changelog",
        "/complaints",
        "/feedback",
        "/join-waitlist",
        "/model-card",
        "/msa",
        "/pricing",
        "/privacy",
        "/terms",
        "/trust",
        "/errors",
        PATH_ORACLE_ACCURACY,
        "/discipline-mirror",
        "/kill-rate",
        "/contradiction-replay",
        "/proof-arena",
        "/since-you-left",
        "/anti-hype",
        "/corpus-passport",
        "/miss-feed",
        "/coverage-honesty",
        "/priority-chain",
        "/zero-tolerance",
        "/emotion-tax",
        "/b2b/committee-one-pager",
        "/allocator-receipt",
        "/transfer-intent",
        "/silence-index",
        "/alert-passport",
        "/visibility-cost",
        "/il-simulator",
        "/market-intelligence",
        "/intelligence-ledger",
        "/address-intelligence",
        "/validity-decay",
        "/desk-duel",
        "/trust-debt",
        "/unique-ten",
        "/d5-honesty",
    }
)

PUBLIC_HTML_PREFIXES: tuple[str, ...] = (
    "/oracle/",
)

# Launch-57 anonymous public API — explicit paths only (SPEC_02 §22; no broad prefix).
LAUNCH57_PUBLIC_API_EXACT: frozenset[str] = frozenset(
    {
        "/api/launch57/guest-trust",
        "/api/launch57/capability-library",
    }
)

LAUNCH57_PUBLIC_API_PREFIXES: tuple[str, ...] = (
    "/api/launch57/capability-library/",
)

# --- Evidence/read API prefixes (historical public developer surface) ---
PUBLIC_API_PREFIXES: tuple[str, ...] = (
    "/health/",
    PATH_API_TRUST_OS,
    *LAUNCH57_PUBLIC_API_PREFIXES,
    "/api/strategy/",
    "/api/intent/",
    "/api/execution/",
    "/api/acceptance/",
    "/api/heroes/",
    "/api/ledger/",
    "/api/glass-box/",
    "/api/audit-challenge",
    "/api/accuracy/",
    "/api/compliance/",
    "/api/security/status",
    "/api/security/external-review-readiness",
    "/api/platform/production-readiness",
    "/api/scale/",
    "/api/viral/",
    "/api/oracle/accuracy",
    "/api/oracle/audit-chain",
    "/api/oracle/half-life",
    "/api/public/",
    "/api/oracle/provenance-score",
    "/api/emotion-tax/",
    "/api/contradiction-replay",
    "/api/proof-arena/",
    "/api/since-you-left",
    "/api/anti-hype/",
    "/api/wow/",
    "/api/due-diligence/evidence-pack/public-summary",
    "/api/due-diligence/corpus-passport/public",
    "/api/locked-predictions",
    "/api/audience/",
        "/api/alerts/generosity",
        "/api/mev/sandwich-report",
        "/api/whale/stealth-advisor",
        "/api/fund/emerging-terminal",
    "/api/auth/oauth/status",
    "/oracle/",
)

PUBLIC_API_EXACT: frozenset[str] = frozenset(
    {
        PATH_API_TRUST_OS,
        *LAUNCH57_PUBLIC_API_EXACT,
        "/api/audit-challenge",
        "/api/security/status",
        "/api/security/external-review-readiness",
        "/api/platform/production-readiness",
        "/api/scale/readiness",
        "/api/viral/readiness",
        "/api/docs/public-openapi.json",
        "/api/docs/public-manifest",
        "/api/status",
        "/api/site-services",
        "/api/changelog",
        "/api/faq",
        "/api/dashboard/stream",
        "/api/product/public-readiness",
        "/capabilities",
        "/compliance",
        "/data-room",
        PATH_ORACLE_ACCURACY,
        "/discipline-mirror",
        "/kill-rate",
        "/contradiction-replay",
        "/proof-arena",
        "/since-you-left",
        "/anti-hype",
        "/corpus-passport",
        "/miss-feed",
        "/coverage-honesty",
        "/priority-chain",
        "/zero-tolerance",
        "/emotion-tax",
        "/api/public/cso-priority-closure",
        "/api/public/zero-tolerance-closure",
        "/api/strategy/priority-chain",
        "/api/strategy/zero-tolerance",
        "/b2b/committee-one-pager",
        "/docs",
        "/docs/public",
    }
)

# Server callbacks — not anonymous visitor surface; bypass session gate only.
INTERNAL_UNAUTHENTICATED_EXACT: frozenset[str] = frozenset(
    {
        "/webhook",
        "/webhook/lemon",
    }
)

INTERNAL_UNAUTHENTICATED_PREFIXES: tuple[str, ...] = (
    "/api/webhooks/",
)

ADMIN_PATH_PREFIXES: tuple[str, ...] = (
    "/admin/",
    "/api/admin/",
)

ADMIN_PATH_EXACT: frozenset[str] = frozenset(
    {
        "/admin/launch",
        "/admin/plan",
        "/admin/roadmap",
    }
)

AUTHENTICATED_PATH_PREFIXES: tuple[str, ...] = (
    "/api/user/",
    "/api/privacy/",
    "/api/billing/",
    "/api/institutional/",
    "/api/cap646/",
    "/api/platform/keys/",
    "/api/journal",
    "/profile",
    "/dashboard",
    "/app",
    "/my/",
)

PRIVATE_DATA_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r'"email"\s*:\s*"[^"]+@[^"]+"', re.I),
    re.compile(r'"api_key"\s*:\s*"[A-Za-z0-9_\-]{8,}"', re.I),
    re.compile(r'"bd_token"\s*:\s*"', re.I),
    re.compile(r'"password"\s*:\s*"', re.I),
    re.compile(r'"session_token"\s*:\s*"', re.I),
)

ANONYMOUS_ROUTE_ALLOWLIST_EXACT: frozenset[str] = (
    INFRASTRUCTURE_EXACT
    | AUTH_FLOW_EXACT
    | PUBLIC_HTML_EXACT
    | PUBLIC_API_EXACT
)

ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES: tuple[str, ...] = (
    INFRASTRUCTURE_PREFIXES
    + AUTH_FLOW_PREFIXES
    + PUBLIC_HTML_PREFIXES
    + PUBLIC_API_PREFIXES
)


def resolve_product_auth_state(user: Mapping[str, Any] | None) -> ProductAuthState:
    if user is None:
        return ProductAuthState.ANONYMOUS
    if user.get("org_id") or user.get("institutional") or user.get("is_institutional"):
        return ProductAuthState.INSTITUTIONAL
    tier = str(user.get("tier") or "free").lower()
    if tier in {"pro", "whale"}:
        return ProductAuthState.PAID_INDIVIDUAL
    return ProductAuthState.FREE_ACCOUNT


def _path_matches(path: str, exact: frozenset[str], prefixes: Iterable[str]) -> bool:
    if path in exact:
        return True
    return any(path.startswith(prefix) for prefix in prefixes)


def is_internal_unauthenticated_route(path: str) -> bool:
    return _path_matches(path, INTERNAL_UNAUTHENTICATED_EXACT, INTERNAL_UNAUTHENTICATED_PREFIXES)


def is_anonymous_route_allowed(method: str, path: str) -> bool:
    if method.upper() == "OPTIONS":
        return True
    if is_internal_unauthenticated_route(path):
        return True
    return _path_matches(path, ANONYMOUS_ROUTE_ALLOWLIST_EXACT, ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES)


def path_is_public(path: str) -> bool:
    """Public visitor/docs surface — excludes internal server callbacks."""
    if is_internal_unauthenticated_route(path):
        return False
    return _path_matches(path, ANONYMOUS_ROUTE_ALLOWLIST_EXACT, ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES)


def classify_route(path: str) -> RouteAccessClass:
    if is_internal_unauthenticated_route(path):
        return RouteAccessClass.INTERNAL
    if _path_matches(path, ADMIN_PATH_EXACT, ADMIN_PATH_PREFIXES):
        return RouteAccessClass.ADMIN
    if is_anonymous_route_allowed("GET", path):
        return RouteAccessClass.PUBLIC
    if _path_matches(path, frozenset(), AUTHENTICATED_PATH_PREFIXES):
        return RouteAccessClass.AUTHENTICATED
    return RouteAccessClass.PRIVATE


def classify_data_class(path: str, access: RouteAccessClass) -> RouteDataClass:
    if access == RouteAccessClass.INTERNAL:
        return RouteDataClass.INTERNAL_CALLBACK
    if access == RouteAccessClass.ADMIN:
        return RouteDataClass.ADMIN_SENSITIVE
    if _path_matches(path, AUTH_FLOW_EXACT, AUTH_FLOW_PREFIXES):
        return RouteDataClass.AUTH_FLOW
    if _path_matches(path, INFRASTRUCTURE_EXACT, INFRASTRUCTURE_PREFIXES):
        return RouteDataClass.INFRASTRUCTURE
    if access == RouteAccessClass.PUBLIC:
        return RouteDataClass.PUBLIC_INTELLIGENCE
    if access in {RouteAccessClass.AUTHENTICATED, RouteAccessClass.PRIVATE}:
        return RouteDataClass.USER_PRIVATE
    return RouteDataClass.MIXED


def request_has_authentication_signal(request: Request) -> bool:
    auth = (request.headers.get("authorization") or "").strip()
    if auth.lower().startswith("bearer ") and len(auth) > 7:
        return True
    if request.cookies.get("bd_token"):
        return True
    if request.query_params.get("api_key"):
        return True
    if request.headers.get("X-Admin-Key"):
        return True
    return False


def enforce_anonymous_route_boundary(request: Request) -> Response | None:
    """Server-side PRIVATE_BY_DEFAULT gate for cookie-less unauthenticated requests."""
    if not PRIVATE_BY_DEFAULT:
        return None
    if request_has_authentication_signal(request):
        return None
    path = request.url.path or ""
    method = request.method or "GET"
    if is_anonymous_route_allowed(method, path):
        return None
    return JSONResponse(
        status_code=401,
        content={
            "detail": "Anonymous access denied",
            "auth_state_required": ProductAuthState.ANONYMOUS.value,
            "expected_auth_state": "AUTHENTICATED_OR_ALLOWLISTED_PUBLIC",
            "path": path,
        },
        headers={"X-Blackdark-Auth-Boundary": "anonymous-denied"},
    )


def build_route_inventory(app: Any) -> list[dict[str, Any]]:
    """Authoritative inventory from FastAPI OpenAPI + non-OpenAPI streams."""
    schema = app.openapi()
    inventory: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for path, spec in (schema.get("paths") or {}).items():
        for method, _operation in spec.items():
            if method.lower() == "parameters":
                continue
            method_u = method.upper()
            key = (method_u, path)
            if key in seen:
                continue
            seen.add(key)
            access = classify_route(path)
            inventory.append(_inventory_row(method_u, path, access))

    for route in getattr(app, "routes", []):
        route_type = type(route).__name__
        path = getattr(route, "path", "") or ""
        if "WebSocket" in route_type and path:
            key = ("WEBSOCKET", path)
            if key not in seen:
                seen.add(key)
                access = classify_route(path)
                inventory.append(_inventory_row("WEBSOCKET", path, access))
        elif "Mount" in route_type and path == "/static":
            key = ("GET", "/static/")
            if key not in seen:
                seen.add(key)
                inventory.append(_inventory_row("GET", "/static/", RouteAccessClass.PUBLIC))

    inventory.sort(key=lambda row: (row["PATH"], row["METHOD"]))
    return inventory


def _inventory_row(method: str, path: str, access: RouteAccessClass) -> dict[str, Any]:
    data_class = classify_data_class(path, access)
    public_allowed = access == RouteAccessClass.PUBLIC
    expected_auth = (
        ProductAuthState.ANONYMOUS.value
        if public_allowed
        else ("ADMIN" if access == RouteAccessClass.ADMIN else "AUTHENTICATED")
    )
    if access == RouteAccessClass.INTERNAL:
        expected_auth = "INTERNAL_CALLBACK"
    owner = _route_owner(path, access)
    return {
        "METHOD": method,
        "PATH": path,
        "EXPECTED_AUTH_STATE": expected_auth,
        "ACTUAL_NO_COOKIE_RESPONSE": None,
        "PUBLIC_ALLOWED": public_allowed,
        "DATA_CLASS": data_class.value,
        "OWNER": owner,
        "TEST_EVIDENCE": f"tests/test_p0_anonymous_route_foundation.py::{_test_slug(path, method)}",
        "ACCESS_CLASS": access.value,
        "RATE_LIMIT_OWNER": "viral_capacity",
        "RATE_LIMIT_STATUS": "deferred_p1",
        "LICENSING_OWNER": "data_governance",
        "LICENSING_STATUS": "deferred_p1",
        "CACHE_OWNER": "wave_00_hardening",
        "CACHE_STATUS": "deferred_p1",
    }


def _route_owner(path: str, access: RouteAccessClass) -> str:
    if path.startswith("/api/auth"):
        return "api.routers.auth"
    if path.startswith("/api/platform"):
        return "platform_api"
    if path.startswith("/api/institutional"):
        return "api.routers.institutional"
    if path.startswith("/api/cap646"):
        return "api.routers.cap646"
    if path.startswith("/admin") or access == RouteAccessClass.ADMIN:
        return "security_auth"
    if access == RouteAccessClass.INTERNAL:
        return "webhook_integrations"
    if path.startswith("/api/"):
        return "dashboard.api"
    return "dashboard.html"


def _test_slug(path: str, method: str) -> str:
    slug = path.strip("/").replace("/", "_").replace("{", "").replace("}", "") or "root"
    return f"test_no_cookie_boundary_{method.lower()}_{slug}"


def response_contains_private_data(payload: str) -> bool:
    return any(pattern.search(payload) for pattern in PRIVATE_DATA_PATTERNS)


def summarize_inventory(inventory: list[dict[str, Any]]) -> dict[str, int]:
    public = sum(1 for row in inventory if row["PUBLIC_ALLOWED"])
    private_protected = sum(
        1
        for row in inventory
        if not row["PUBLIC_ALLOWED"] and row["ACCESS_CLASS"] in {"private", "authenticated", "admin"}
    )
    return {
        "ROUTES_INVENTORIED": len(inventory),
        "PUBLIC_EXPLICIT": public,
        "PRIVATE_PROTECTED": private_protected,
    }
