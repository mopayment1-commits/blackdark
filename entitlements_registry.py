"""
Feature entitlements SSOT — keyed by internal plan id (billing/plan_registry).

Do not branch on marketing tier names in product code; use feature keys only.
"""

from __future__ import annotations

from typing import Any, Final

# Limit sentinel: unlimited capacity for watchlist / alerts / history / compare.
UNLIMITED: Final[int] = -1

ENTITLEMENT_FEATURE_KEYS: Final[tuple[str, ...]] = (
    "watchlist_limit",
    "alerts_limit",
    "history_limit",
    "compare_limit",
    "offline",
    "share_decision",
    "theme",
    "charts",
    "api_read",
    "api_full",
    "certificate_export",
    "advanced_alerts",
    "saved_language",
    "oracle_btc_eth_only",
)

# Keys with int limits (0 = disabled, UNLIMITED = no cap).
_LIMIT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "watchlist_limit",
        "alerts_limit",
        "history_limit",
        "compare_limit",
    }
)

_BOOL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "offline",
        "share_decision",
        "theme",
        "charts",
        "api_read",
        "api_full",
        "certificate_export",
        "advanced_alerts",
        "saved_language",
        "oracle_btc_eth_only",
    }
)

_PLAN_ENTITLEMENTS: dict[str, dict[str, int | bool]] = {
    "free": {
        "watchlist_limit": 0,
        "alerts_limit": 0,
        "history_limit": 0,
        "compare_limit": 0,
        "offline": False,
        "share_decision": False,
        "theme": False,
        "charts": False,
        "api_read": False,
        "api_full": False,
        "certificate_export": False,
        "advanced_alerts": False,
        "saved_language": True,
        "oracle_btc_eth_only": True,
    },
    "pro": {
        "watchlist_limit": 5,
        "alerts_limit": 1,
        "history_limit": 20,
        "compare_limit": 2,
        "offline": True,
        "share_decision": False,
        "theme": False,
        "charts": False,
        "api_read": False,
        "api_full": False,
        "certificate_export": False,
        "advanced_alerts": False,
        "saved_language": True,
        "oracle_btc_eth_only": False,
    },
    "elite": {
        "watchlist_limit": 20,
        "alerts_limit": UNLIMITED,
        "history_limit": UNLIMITED,
        "compare_limit": 5,
        "offline": True,
        "share_decision": True,
        "theme": True,
        "charts": True,
        "api_read": False,
        "api_full": False,
        "certificate_export": False,
        "advanced_alerts": False,
        "saved_language": True,
        "oracle_btc_eth_only": False,
    },
    "quant": {
        "watchlist_limit": UNLIMITED,
        "alerts_limit": UNLIMITED,
        "history_limit": UNLIMITED,
        "compare_limit": 5,
        "offline": True,
        "share_decision": True,
        "theme": True,
        "charts": True,
        "api_read": True,
        "api_full": False,
        "certificate_export": True,
        "advanced_alerts": True,
        "saved_language": True,
        "oracle_btc_eth_only": False,
    },
    "institutional": {
        "watchlist_limit": UNLIMITED,
        "alerts_limit": UNLIMITED,
        "history_limit": UNLIMITED,
        "compare_limit": UNLIMITED,
        "offline": True,
        "share_decision": True,
        "theme": True,
        "charts": True,
        "api_read": True,
        "api_full": True,
        "certificate_export": True,
        "advanced_alerts": True,
        "saved_language": True,
        "oracle_btc_eth_only": False,
    },
}

# Legacy tier aliases share the same entitlement row as canonical plan.
for _alias, _canonical in (
    ("whale", "elite"),
    ("decision_pro", "pro"),
    ("decision_desk", "quant"),
    ("proof_pass", "free"),
):
    if _alias not in _PLAN_ENTITLEMENTS and _canonical in _PLAN_ENTITLEMENTS:
        _PLAN_ENTITLEMENTS[_alias] = dict(_PLAN_ENTITLEMENTS[_canonical])


def normalize_entitlement_plan(plan: str | None) -> str:
    from billing.plan_registry import normalize_plan

    return normalize_plan(plan)


def entitlements_for_plan(plan: str | None) -> dict[str, int | bool]:
    key = normalize_entitlement_plan(plan)
    base = _PLAN_ENTITLEMENTS.get(key) or _PLAN_ENTITLEMENTS["free"]
    return dict(base)


def entitlement_catalog() -> dict[str, Any]:
    return {
        "feature_keys": list(ENTITLEMENT_FEATURE_KEYS),
        "unlimited_sentinel": UNLIMITED,
        "plans": {pid: dict(row) for pid, row in _PLAN_ENTITLEMENTS.items() if pid in {
            "free", "pro", "elite", "quant", "institutional"
        }},
    }
