"""Flash-crash protection — velocity, spread explosion, book collapse, feed divergence."""

from __future__ import annotations

from typing import Any

from confidence_truth import claim_heuristic, claim_insufficient
from risk_intelligence import flash_crash_risk


def detect_flash_crash(
    *,
    returns_bps: list[float],
    window_sec: float,
    spread_bps_now: float | None = None,
    spread_bps_baseline: float | None = None,
    depth_now: float | None = None,
    depth_baseline: float | None = None,
    venue_mids: dict[str, float] | None = None,
) -> dict[str, Any]:
    base = flash_crash_risk(returns_bps=returns_bps, window_sec=window_sec)
    signals: list[str] = []
    if base.get("elevated"):
        signals.append("price_velocity")
    if (
        spread_bps_now is not None
        and spread_bps_baseline is not None
        and spread_bps_baseline > 0
        and spread_bps_now >= spread_bps_baseline * 5
    ):
        signals.append("spread_explosion")
    if (
        depth_now is not None
        and depth_baseline is not None
        and depth_baseline > 0
        and depth_now <= depth_baseline * 0.2
    ):
        signals.append("order_book_collapse")
    if venue_mids and len(venue_mids) >= 2:
        vals = list(venue_mids.values())
        mid = sum(vals) / len(vals)
        if mid > 0:
            divergences = [abs(v - mid) / mid * 10_000 for v in vals]
            if max(divergences) >= 75:
                signals.append("provider_divergence")
    blocked = bool(signals) or base.get("gate") in {"block", "fail_closed"}
    return {
        "kind": "flash_crash_protection",
        "signals": signals,
        "base": base,
        "gate": "block" if blocked else "pass",
        "executable": not blocked,
        "protects": ["automated_decisions", "execution", "portfolio_actions"],
        "score": claim_heuristic(min(1.0, 0.25 * len(signals)), label="flash_signals").to_dict()
        if signals
        else claim_insufficient(label="flash_signals", notes="no_elevated_signals").to_dict(),
    }


def flash_crash_status() -> dict[str, Any]:
    return {
        "surface": "flash_crash_protection",
        "product_complete": False,
        "signals": [
            "price_velocity",
            "spread_explosion",
            "order_book_collapse",
            "liquidity_disappearance",
            "provider_divergence",
        ],
    }
