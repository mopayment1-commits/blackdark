"""Fallback, degradation, and abstention policies."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from data_governance.registry import get_registry_entry


class FallbackClass(StrEnum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    DERIVED_FALLBACK = "DERIVED_FALLBACK"
    NO_SAFE_FALLBACK = "NO_SAFE_FALLBACK"


CRITICAL_DEPENDENCIES: dict[str, dict[str, Any]] = {
    "live_quotes": {
        "primary": "binance_ws",
        "secondary": "binance_spot",
        "derived_fallback": "coingecko_prices",
        "no_safe_fallback_action": "ABSTAIN",
    },
    "execution_depth": {
        "primary": "live_book_hub",
        "secondary": "binance_spot",
        "derived_fallback": None,
        "no_safe_fallback_action": "DEGRADED",
    },
    "reference_price": {
        "primary": "coingecko_prices",
        "secondary": "binance_spot",
        "derived_fallback": "kraken_spot",
        "no_safe_fallback_action": "ABSTAIN",
    },
}


def resolve_fallback(source_id: str, *, health: str = "healthy") -> dict[str, Any]:
    entry = get_registry_entry(source_id)
    if health == "healthy":
        return {"action": "use_primary", "source_id": source_id, "state": "ADMITTED"}
    fallbacks = list(entry.fallback_sources) if entry else []
    if fallbacks:
        return {"action": "fallback", "source_id": fallbacks[0], "from": source_id, "state": "DEGRADED"}
    return {"action": "abstain", "source_id": source_id, "state": "ABSTAINED", "reason": "no_safe_fallback"}


def evaluate_fallback(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    freshness = out.get("freshness_state") or (out.get("data_governance_freshness") or {}).get("freshness_state")
    if freshness in {"STALE", "UNKNOWN"}:
        fb = resolve_fallback("binance_ws", health="unhealthy")
        out["fallback_policy"] = fb
        out["degraded_mode"] = fb["state"] == "DEGRADED"
        if fb["state"] == "ABSTAINED":
            out["abstain_reason"] = "insufficient_fresh_inputs"
    else:
        out["fallback_policy"] = {"action": "use_primary", "state": "ADMITTED"}
    return out
