"""Canonical ANONYMOUS_ROUTE_ALLOWLIST — AV §17 deny-by-default."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AnonymousRouteEntry:
    method: str
    path: str
    expected_auth_state: str = "ANONYMOUS"
    data_class: str = "PUBLIC_INTELLIGENCE"
    rate_limit_per_min: int = 120
    burst_limit: int = 30
    concurrency_limit: int = 20
    upstream_cost_budget: int = 5
    response_size_limit_kb: int = 512
    cache_policy: str = "public,max-age=45,stale-while-revalidate=120"
    timeout_sec: float = 15.0
    owner: str = "anonymous_visitor"
    license_source_id: str | None = None
    test_evidence: str = "tests/test_anonymous_visitor_av_matrix.py"


def _e(
    method: str,
    path: str,
    *,
    data_class: str = "PUBLIC_INTELLIGENCE",
    rate: int = 120,
    burst: int = 30,
    cost: int = 5,
    cache: str = "public,max-age=45,stale-while-revalidate=120",
    owner: str = "anonymous_visitor",
    license_source_id: str | None = None,
) -> AnonymousRouteEntry:
    return AnonymousRouteEntry(
        method=method.upper(),
        path=path,
        data_class=data_class,
        rate_limit_per_min=rate,
        burst_limit=burst,
        upstream_cost_budget=cost,
        cache_policy=cache,
        owner=owner,
        license_source_id=license_source_id,
    )


# Single canonical allowlist — no parallel registries.
ANONYMOUS_ROUTE_ALLOWLIST: tuple[AnonymousRouteEntry, ...] = (
    # Health / platform
    _e("GET", "/health", data_class="OPERATIONAL", rate=600, owner="platform"),
    _e("GET", "/health/live", data_class="OPERATIONAL", rate=600, owner="platform"),
    _e("GET", "/health/ready", data_class="OPERATIONAL", rate=600, owner="platform"),
    _e("GET", "/health/viral", data_class="OPERATIONAL", rate=600, owner="platform"),
    _e("GET", "/api/security/status", data_class="OPERATIONAL", rate=120, owner="security"),
    _e("GET", "/api/platform/production-readiness", data_class="OPERATIONAL", rate=60, owner="platform"),
    # Landing + public HTML shells
    _e("GET", "/", data_class="PUBLIC_MARKETING", rate=240, cache="public,max-age=45", owner="landing"),
    _e("GET", "/capabilities", data_class="PUBLIC_MARKETING", rate=120, owner="landing"),
    _e("GET", "/compliance", data_class="PUBLIC_MARKETING", rate=120, owner="landing"),
    _e("GET", "/docs", data_class="PUBLIC_MARKETING", rate=120, owner="landing"),
    _e("GET", "/docs/public", data_class="PUBLIC_MARKETING", rate=120, owner="landing"),
    _e("GET", "/oracle-accuracy", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/kill-rate", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/proof-arena", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/methodology", data_class="PUBLIC_EVIDENCE", rate=120, owner="landing"),
    _e("GET", "/accuracy", data_class="PUBLIC_EVIDENCE", rate=120, owner="landing"),
    _e("GET", "/status", data_class="PUBLIC_EVIDENCE", rate=120, owner="landing"),
    _e("GET", "/markets", data_class="PUBLIC_MARKET", rate=120, owner="market"),
    # i18n + auth status (no personalization)
    _e("GET", "/api/i18n/locales", data_class="PUBLIC_UTILITY", rate=120, owner="i18n"),
    _e("GET", "/api/i18n/catalog", data_class="PUBLIC_UTILITY", rate=120, owner="i18n"),
    _e("GET", "/api/auth/oauth/status", data_class="PUBLIC_UTILITY", rate=60, owner="auth"),
    _e("GET", "/api/institutional/sso/status", data_class="PUBLIC_UTILITY", rate=60, owner="institutional"),
    # Trust Pulse — public product proof
    _e("GET", "/api/trust-pulse", data_class="PUBLIC_INTELLIGENCE", rate=60, cost=3, license_source_id="oracle_unified"),
    _e("GET", "/api/trust-pulse/manifest", data_class="PUBLIC_INTELLIGENCE", rate=120, owner="trust_pulse"),
    _e("GET", "/api/trust-pulse/stream", data_class="PUBLIC_STREAM", rate=30, cost=2, owner="trust_pulse"),
    # Anonymous visitor public intelligence API
    _e("GET", "/api/anonymous-visitor/status", data_class="OPERATIONAL", rate=120),
    _e("GET", "/api/anonymous-visitor/states", data_class="OPERATIONAL", rate=120),
    _e("GET", "/api/anonymous-visitor/allowlist", data_class="OPERATIONAL", rate=60),
    _e("GET", "/api/anonymous-visitor/route-inventory", data_class="OPERATIONAL", rate=30, owner="governance"),
    _e("GET", "/api/anonymous-visitor/matrix", data_class="OPERATIONAL", rate=60),
    _e("GET", "/api/anonymous-visitor/evidence", data_class="OPERATIONAL", rate=60),
    _e("GET", "/api/anonymous-visitor/public-intelligence/decision-truth-pulse", data_class="PUBLIC_INTELLIGENCE", rate=60, license_source_id="oracle_unified"),
    _e("GET", "/api/anonymous-visitor/public-intelligence/evidence-passport", data_class="PUBLIC_INTELLIGENCE", rate=60, license_source_id="data_governance_registry"),
    _e("GET", "/api/anonymous-visitor/public-intelligence/net-edge-proof", data_class="PUBLIC_INTELLIGENCE", rate=60, license_source_id="oracle_unified"),
    _e("GET", "/api/anonymous-visitor/public-intelligence/market-surface", data_class="PUBLIC_MARKET", rate=60, license_source_id="market_context"),
    _e("GET", "/api/anonymous-visitor/public-intelligence/accuracy", data_class="PUBLIC_EVIDENCE", rate=60, license_source_id="oracle_audit_chain"),
    _e("GET", "/api/anonymous-visitor/public-intelligence/methodology", data_class="PUBLIC_EVIDENCE", rate=60),
    _e("GET", "/api/anonymous-visitor/consent/status", data_class="PUBLIC_UTILITY", rate=120),
    _e("POST", "/api/anonymous-visitor/consent", data_class="PUBLIC_UTILITY", rate=30),
    _e("POST", "/api/anonymous-visitor/analytics/event", data_class="PUBLIC_UTILITY", rate=60),
    _e("GET", "/api/anonymous-visitor/seo/policy", data_class="PUBLIC_UTILITY", rate=60),
    _e("GET", "/api/anonymous-visitor/accessibility/report", data_class="PUBLIC_UTILITY", rate=30),
    _e("GET", "/api/anonymous-visitor/licensing/register", data_class="PUBLIC_UTILITY", rate=60),
    # Evidence / read APIs (existing public surfaces)
    _e("GET", "/api/trust-os", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/public/kill-rate", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/public/miss-feed", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/public/coverage-honesty", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/public/brand-coverage-closure", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/public/cso-priority-closure", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/public/zero-tolerance-closure", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/public/changed-mind", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/public/decision-graph", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes"),
    _e("GET", "/api/oracle/audit-chain", data_class="PUBLIC_EVIDENCE", rate=60, license_source_id="oracle_audit_chain", owner="oracle"),
    _e("GET", "/api/oracle/half-life", data_class="PUBLIC_EVIDENCE", rate=60, owner="oracle"),
    _e("GET", "/api/oracle/accuracy", data_class="PUBLIC_EVIDENCE", rate=60, owner="oracle"),
    _e("GET", "/api/due-diligence/evidence-pack/public-summary", data_class="PUBLIC_EVIDENCE", rate=60, owner="observability"),
    _e("GET", "/api/due-diligence/corpus-passport/public", data_class="PUBLIC_EVIDENCE", rate=60, owner="observability"),
    _e("GET", "/api/docs/public-openapi.json", data_class="PUBLIC_UTILITY", rate=30, owner="public_api_docs"),
    # Landing page public surfaces (explicit classification + RL guards)
    _e("GET", "/api/pricing", data_class="PUBLIC_MARKETING", rate=60, owner="billing"),
    _e("GET", "/api/billing/payments", data_class="PUBLIC_MARKETING", rate=60, owner="billing"),
    _e("POST", "/api/billing/institutional-inquiry", data_class="PUBLIC_UTILITY", rate=30, owner="billing"),
    _e("POST", "/api/analytics/view", data_class="PUBLIC_UTILITY", rate=120, owner="analytics"),
    _e("GET", "/api/analytics/stats", data_class="PUBLIC_UTILITY", rate=60, owner="analytics"),
    _e("GET", "/api/platform/stats", data_class="PUBLIC_UTILITY", rate=60, owner="platform"),
    _e("GET", "/api/telegram/free/status", data_class="PUBLIC_UTILITY", rate=60, owner="telegram"),
    _e("GET", "/api/audience/entry", data_class="PUBLIC_UTILITY", rate=60, owner="audience"),
    _e("POST", "/api/discipline-mirror/answer", data_class="PUBLIC_UTILITY", rate=30, owner="discipline_mirror"),
    _e("POST", "/join-waitlist", data_class="PUBLIC_UTILITY", rate=30, owner="landing"),
    # Oracle HTML + API prefix reads
    _e("GET", "/oracle/{symbol}", data_class="PUBLIC_INTELLIGENCE", rate=60, owner="oracle"),
    _e("GET", "/oracle/{symbol}/quick", data_class="PUBLIC_INTELLIGENCE", rate=60, owner="oracle"),
)

# Prefix-based anonymous allowances (explicit declaration only).
ANONYMOUS_PREFIX_ALLOWLIST: tuple[tuple[str, str, AnonymousRouteEntry], ...] = (
    ("GET", "/health/", _e("GET", "/health/*", data_class="OPERATIONAL", rate=600, owner="platform")),
    ("GET", "/static/", _e("GET", "/static/*", data_class="PUBLIC_ASSET", rate=600, owner="static")),
    ("GET", "/api/heroes/", _e("GET", "/api/heroes/*", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes")),
    ("GET", "/api/strategy/", _e("GET", "/api/strategy/*", data_class="PUBLIC_EVIDENCE", rate=120, owner="compounding")),
    ("GET", "/api/glass-box/", _e("GET", "/api/glass-box/*", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes")),
    ("GET", "/api/accuracy/", _e("GET", "/api/accuracy/*", data_class="PUBLIC_EVIDENCE", rate=120, owner="heroes")),
    ("GET", "/api/locked-predictions", _e("GET", "/api/locked-predictions", data_class="PUBLIC_EVIDENCE", rate=60, owner="heroes")),
    ("GET", "/api/viral/", _e("GET", "/api/viral/*", data_class="PUBLIC_EVIDENCE", rate=60, owner="viral")),
    ("GET", "/api/scale/", _e("GET", "/api/scale/*", data_class="PUBLIC_EVIDENCE", rate=60, owner="platform")),
)

# Paths always private for anonymous — server-side deny even if handler lacks auth.
# Hard server-side deny for anonymous — accidental exposure fixes (AV §17/§18).
ANONYMOUS_DENY_PREFIXES: tuple[str, ...] = (
    "/api/data-governance",
    "/api/financial-data-security",
    "/api/user",
    "/api/privacy",
    "/api/admin",
    "/api/institutional",
    "/api/v1/admin",
    "/metrics",
)

# Full OpenAPI schema — authenticated/ops only; public filtered schema stays allowlisted.
ANONYMOUS_DENY_EXACT: frozenset[str] = frozenset(
    {
        "/openapi.json",
        "/api/docs/openapi.json",
    }
)

# Explicit anonymous exceptions to hard deny prefixes.
ANONYMOUS_DENY_EXCEPTIONS: frozenset[str] = frozenset(
    {
        "/api/institutional/sso/status",
    }
)

# HTML pages that must not be indexed / require account for depth.
PRIVATE_HTML_PREFIXES: tuple[str, ...] = (
    "/dashboard",
    "/account",
    "/billing",
    "/portfolio",
    "/settings",
    "/admin",
)


def _normalize_path(path: str) -> str:
    p = (path or "/").split("?", 1)[0]
    if not p.startswith("/"):
        p = f"/{p}"
    if len(p) > 1 and p.endswith("/"):
        p = p.rstrip("/")
    return p


def exact_allowlist_index() -> dict[tuple[str, str], AnonymousRouteEntry]:
    return {(e.method.upper(), _normalize_path(e.path)): e for e in ANONYMOUS_ROUTE_ALLOWLIST}


def is_anonymous_denied(path: str) -> bool:
    p = _normalize_path(path)
    if p in ANONYMOUS_DENY_EXCEPTIONS:
        return False
    if p in ANONYMOUS_DENY_EXACT:
        return True
    return any(p == pref or p.startswith(pref.rstrip("/") + "/") or p.startswith(pref) for pref in ANONYMOUS_DENY_PREFIXES)


def match_allowlist_entry(method: str, path: str) -> AnonymousRouteEntry | None:
    m = method.upper()
    p = _normalize_path(path)
    hit = exact_allowlist_index().get((m, p))
    if hit:
        return hit
    for pm, prefix, entry in ANONYMOUS_PREFIX_ALLOWLIST:
        if m == pm and p.startswith(prefix):
            return entry
    # Template paths like /oracle/{symbol}
    for entry in ANONYMOUS_ROUTE_ALLOWLIST:
        if "{" not in entry.path:
            continue
        if m != entry.method:
            continue
        parts = entry.path.strip("/").split("/")
        actual = p.strip("/").split("/")
        if len(parts) != len(actual):
            continue
        if all(a == b or b.startswith("{") and b.endswith("}") for a, b in zip(actual, parts, strict=False)):
            return entry
    return None


def is_anonymous_allowed(method: str, path: str) -> bool:
    p = _normalize_path(path)
    if is_anonymous_denied(p):
        return False
    if match_allowlist_entry(method, p):
        return True
    # Non-API HTML GET pages outside deny list are public marketing unless private prefix.
    if method.upper() == "GET" and not p.startswith("/api/"):
        if any(p == pref or p.startswith(pref + "/") for pref in PRIVATE_HTML_PREFIXES):
            return False
        return True
    return False


def path_is_anonymous_public(path: str) -> bool:
    """OpenAPI/public-docs helper — any method allowed on path."""
    if is_anonymous_denied(path):
        return False
    if match_allowlist_entry("GET", path) or match_allowlist_entry("POST", path):
        return True
    for _, prefix, _ in ANONYMOUS_PREFIX_ALLOWLIST:
        if path.startswith(prefix):
            return True
    p = _normalize_path(path)
    return not p.startswith("/api/")


def path_is_canonical_public_surface(path: str) -> bool:
    """Strict allowlist-only classification (no implicit HTML public fallback)."""
    if is_anonymous_denied(path):
        return False
    if match_allowlist_entry("GET", path) or match_allowlist_entry("POST", path):
        return True
    return any(path.startswith(prefix) for _, prefix, _ in ANONYMOUS_PREFIX_ALLOWLIST)


def allowlist_export() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in ANONYMOUS_ROUTE_ALLOWLIST:
        rows.append(
            {
                "method": entry.method,
                "path": entry.path,
                "expected_auth_state": entry.expected_auth_state,
                "data_class": entry.data_class,
                "rate_limit_per_min": entry.rate_limit_per_min,
                "burst_limit": entry.burst_limit,
                "concurrency_limit": entry.concurrency_limit,
                "upstream_cost_budget": entry.upstream_cost_budget,
                "response_size_limit_kb": entry.response_size_limit_kb,
                "cache_policy": entry.cache_policy,
                "timeout_sec": entry.timeout_sec,
                "owner": entry.owner,
                "license_source_id": entry.license_source_id,
                "test_evidence": entry.test_evidence,
            }
        )
    return rows
