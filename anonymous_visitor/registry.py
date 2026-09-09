"""Route classification registry — delegates to canonical allowlist only."""

from __future__ import annotations

from typing import Any

from anonymous_visitor.allowlist import (
    ANONYMOUS_DENY_PREFIXES,
    ANONYMOUS_ROUTE_ALLOWLIST,
    is_anonymous_allowed,
    is_anonymous_denied,
    match_allowlist_entry,
)


def _legacy_public_prefix(path: str) -> bool:
    try:
        from public_api_docs import path_is_public

        return path_is_public(path)
    except Exception:
        return False


def classify_route(method: str, path: str) -> dict[str, Any]:
    entry = match_allowlist_entry(method, path)
    denied = is_anonymous_denied(path)
    legacy_public = _legacy_public_prefix(path)
    allowed = is_anonymous_allowed(method, path) or legacy_public
    explicit = entry is not None or denied or legacy_public or path.startswith("/api/auth/")
    return {
        "method": method.upper(),
        "path": path,
        "expected_auth_state": "AUTHENTICATED" if denied else ("ANONYMOUS" if allowed else "AUTHENTICATED"),
        "public_allowed": allowed and not denied,
        "explicit_classification": explicit,
        "deny_prefix_hit": denied,
        "entry": None
        if entry is None
        else {
            "data_class": entry.data_class,
            "rate_limit_per_min": entry.rate_limit_per_min,
            "upstream_cost_budget": entry.upstream_cost_budget,
            "cache_policy": entry.cache_policy,
            "owner": entry.owner,
            "license_source_id": entry.license_source_id,
        },
    }


def registry_summary() -> dict[str, Any]:
    return {
        "canonical_allowlist_entries": len(ANONYMOUS_ROUTE_ALLOWLIST),
        "deny_prefixes": list(ANONYMOUS_DENY_PREFIXES),
        "single_registry": True,
        "parallel_registries": False,
    }
