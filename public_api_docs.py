"""
BLACKDARK — Limited public developer surface (evidence / read APIs).

Full OpenAPI remains available for ops; public docs intentionally omit
execution, billing webhooks, admin, and key-management write paths.

Allowlist owner: anonymous_route_foundation (P0 canonical).
"""

from __future__ import annotations

from typing import Any

from anonymous_route_foundation import (
    ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES,
    PATH_API_TRUST_OS,
    PATH_ORACLE_ACCURACY,
    path_is_public,
)

# Anonymous allowlist includes POST hero endpoints; public *read* docs omit them.
PUBLIC_DOCS_READ_PREFIX_EXCLUDE: frozenset[str] = frozenset(
    {
        "/api/whale/stealth-advisor",
    }
)

# GET probe on the prefix URL (trailing slash as listed). 200/307 → safe page link in /docs.
PUBLIC_DOCS_PREFIX_PAGE_LINK_OK: frozenset[str] = frozenset(
    {
        "/health/",
        "/api/trust-os",
        "/api/launch57/capability-library/",
        "/api/audit-challenge",
        "/api/security/status",
        "/api/security/external-review-readiness",
        "/api/platform/production-readiness",
        "/api/oracle/accuracy",
        "/api/oracle/audit-chain",
        "/api/oracle/half-life",
        "/api/oracle/provenance-score",
        "/api/contradiction-replay",
        "/api/since-you-left",
        "/api/due-diligence/evidence-pack/public-summary",
        "/api/due-diligence/corpus-passport/public",
        "/api/locked-predictions",
        "/api/alerts/generosity",
        "/api/mev/sandwich-report",
        "/api/fund/emerging-terminal",
        "/api/auth/oauth/status",
    }
)

__all__ = [
    "PUBLIC_PATH_PREFIXES",
    "PUBLIC_PATH_EXACT",
    "PATH_API_TRUST_OS",
    "PATH_ORACLE_ACCURACY",
    "path_is_public",
    "filter_openapi_for_public",
    "public_docs_manifest",
]

# Backward-compatible exports for existing imports.
PUBLIC_PATH_PREFIXES: tuple[str, ...] = ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES

PUBLIC_PATH_EXACT: frozenset[str] = frozenset(
    {
        PATH_API_TRUST_OS,
        "/api/audit-challenge",
        "/api/security/status",
        "/api/security/external-review-readiness",
        "/api/platform/production-readiness",
        "/api/scale/readiness",
        "/api/viral/readiness",
        "/health/viral",
        "/api/docs/public-openapi.json",
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


def filter_openapi_for_public(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of OpenAPI limited to evidence/read surfaces."""
    out = dict(schema)
    paths = schema.get("paths") or {}
    public_paths = {p: spec for p, spec in paths.items() if path_is_public(p)}
    out["paths"] = public_paths
    out["info"] = {
        **(schema.get("info") or {}),
        "title": "BLACKDARK Public Evidence API",
        "description": (
            "Read/evidence endpoints only. Not a full execution platform. "
            "Analytical tool — not financial advice. Verify on /oracle-accuracy."
        ),
    }
    out["x-blackdark"] = {
        "surface": "public_developer_docs",
        "policy": "evidence_and_read_only",
        "not_included": [
            "admin",
            "billing_webhooks",
            "user_api_key_write",
            "live_execution_orders",
            "secrets",
        ],
        "verify": PATH_ORACLE_ACCURACY,
    }
    return out


def _dedupe_prefixes(prefixes: tuple[str, ...] | list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for prefix in prefixes:
        if prefix in seen:
            continue
        seen.add(prefix)
        out.append(prefix)
    return out


def public_docs_read_prefixes() -> list[str]:
    """Prefixes shown under /docs (evidence/read); deduped; excludes POST-only surfaces."""
    raw = _dedupe_prefixes(ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES)
    return [p for p in raw if p not in PUBLIC_DOCS_READ_PREFIX_EXCLUDE]


def public_docs_prefix_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in public_docs_read_prefixes():
        row: dict[str, str] = {"path": path}
        if path in PUBLIC_DOCS_PREFIX_PAGE_LINK_OK:
            row["href"] = path
        rows.append(row)
    return rows


def public_docs_manifest() -> dict[str, Any]:
    read_prefixes = public_docs_read_prefixes()
    return {
        "title": "BLACKDARK Public Developer Docs",
        "policy": "evidence_and_read_only",
        "html": "/docs",
        "openapi_json": "/api/docs/public-openapi.json",
        "full_openapi_ops": "/api/docs/openapi.json",
        "allowed_prefixes": read_prefixes,
        "allowed_prefix_rows": public_docs_prefix_rows(),
        "post_only_public_prefixes": sorted(PUBLIC_DOCS_READ_PREFIX_EXCLUDE),
        "primary_surfaces": [
            {"path": PATH_ORACLE_ACCURACY, "role": "Public Accuracy Ledger including misses"},
            {"path": "/errors", "role": "Alias → ledger misses section"},
            {"path": "/discipline-mirror", "role": "Private Discipline Mirror"},
            {"path": PATH_API_TRUST_OS, "role": "Four value layers + denylist"},
            {"path": "/api/glass-box/challenge", "role": "Competitor challenge pack"},
        ],
        "disclaimer": (
            "Not financial advice. Public docs do not expose execution secrets. "
            "Engineering posture ≠ ISO 27001 certificate."
        ),
    }
