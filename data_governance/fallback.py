"""Source redundancy failover (DIG-008, DIG-025, DIG-041)."""

from __future__ import annotations

from typing import Any

_FALLBACK_CHAIN = {
    "coingecko": ["binance", "internal_cache"],
    "binance": ["coingecko", "internal_cache"],
}


def resolve_fallback(source_id: str) -> list[str]:
    return list(_FALLBACK_CHAIN.get(source_id, ["internal_cache"]))


def apply_fallback(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    sid = str(out.get("source_id") or out.get("source") or "internal_cache")
    out["fallback_chain"] = resolve_fallback(sid)
    return out
