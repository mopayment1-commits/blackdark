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


def public_docs_manifest() -> dict[str, Any]:
    return {
        "title": "BLACKDARK Public Developer Docs",
        "policy": "evidence_and_read_only",
        "html": "/docs",
        "openapi_json": "/api/docs/public-openapi.json",
        "full_openapi_ops": "/api/docs/openapi.json",
        "allowed_prefixes": list(ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES),
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
