"""
BLACKDARK — Limited public developer surface (evidence / read APIs).

Full OpenAPI remains available for ops; public docs intentionally omit
execution, billing webhooks, admin, and key-management write paths.
"""

from __future__ import annotations

from typing import Any

# Sonar S1192: duplicated string literals
PATH_API_TRUST_OS = '/api/trust-os'
PATH_ORACLE_ACCURACY = '/oracle-accuracy'

# Path prefixes allowed in the public developer OpenAPI.
PUBLIC_PATH_PREFIXES: tuple[str, ...] = (
    "/api/v1/oracle",
    "/api/v1/accuracy",
    "/api/v1/feed",
    "/api/v1/me",
    "/api/v1/audit",
    "/api/v1/usage",
    "/api/v1/webhooks",
    "/api/v1/changelog",
    PATH_API_TRUST_OS,
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
    "/api/scale/",
    "/api/viral/",
    "/api/oracle/accuracy",
    "/api/oracle/audit-chain",
    "/api/oracle/half-life",
    "/api/public/kill-rate",
    "/api/public/miss-feed",
    "/api/public/coverage-honesty",
    "/api/public/canonical-market-state",
    "/api/public/data-trust-closure",
    "/api/public/brand-coverage-closure",
    "/api/public/cso-priority-closure",
    "/api/public/zero-tolerance-closure",
    "/api/strategy/",
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
    "/api/fund/emerging-terminal",
    "/api/auth/oauth/status",
    "/oracle/",
)

PUBLIC_PATH_EXACT: frozenset[str] = frozenset(
    {
        PATH_API_TRUST_OS,
        "/api/audit-challenge",
        "/api/security/status",
        "/api/scale/readiness",
        "/api/viral/readiness",
        "/health/viral",
        "/api/docs/public-openapi.json",
        "/api/v1",
        "/api/v1/",
        "/api/v1/openapi.json",
        "/api/v1/changelog",
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


def path_is_public(path: str) -> bool:
    if path.startswith("/api/v1/keys"):
        return False
    if path in PUBLIC_PATH_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)


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
        "allowed_prefixes": list(PUBLIC_PATH_PREFIXES),
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
