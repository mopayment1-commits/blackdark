"""
BLACKDARK — M&A Intelligence (CAP PDF #113 / strategic deal signals).

Dedicated module: token merger spreads, acquisition comps, deal-readiness signals.
Not a generic handler — uses acquisition audit pillars + live market context.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.MAIntelligence")

DealSignal = Literal["none", "watch", "elevated", "actionable"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _token_merger_spread_signals(symbol: str) -> dict[str, Any]:
    """Cross-venue price dispersion as proxy for merger/arbitrage spread intelligence."""
    from arbitrage_service import compare_symbol_across_exchanges

    comp = await compare_symbol_across_exchanges(symbol)
    venues = comp.get("venues") or []
    if len(venues) < 2:
        return {
            "signal": "none",
            "spread_bps_max": 0.0,
            "venue_count": len(venues),
            "note": "Insufficient venue coverage for M&A spread signal.",
        }
    bids = [v["best_bid"] for v in venues if v.get("best_bid")]
    asks = [v["best_ask"] for v in venues if v.get("best_ask")]
    if not bids or not asks:
        return {"signal": "none", "spread_bps_max": 0.0, "venue_count": len(venues)}
    max_bid = max(bids)
    min_ask = min(asks)
    spread_bps = ((max_bid - min_ask) / min_ask * 10_000) if min_ask > 0 else 0.0
    signal: DealSignal = "none"
    if spread_bps >= 50:
        signal = "actionable"
    elif spread_bps >= 20:
        signal = "elevated"
    elif spread_bps >= 8:
        signal = "watch"
    return {
        "signal": signal,
        "spread_bps_max": round(spread_bps, 2),
        "best_bid_venue": next((v["exchange"] for v in venues if v.get("best_bid") == max_bid), None),
        "best_ask_venue": next((v["exchange"] for v in venues if v.get("best_ask") == min_ask), None),
        "venue_count": len(venues),
    }


async def _acquisition_comps() -> dict[str, Any]:
    """Strategic buyer comps from acquisition asset audit."""
    from acquisition_assets_service import build_acquisition_asset_audit

    audit = await build_acquisition_asset_audit()
    pillars = audit.get("pillars") or {}
    strong = sum(1 for p in pillars.values() if (p or {}).get("verdict") in {"moderate", "strong"})
    return {
        "deal_verdict": audit.get("deal_verdict"),
        "code_value_estimate_pct": audit.get("code_value_estimate_pct"),
        "strong_pillars": strong,
        "transferable_if_acquired": audit.get("transferable_if_acquired"),
        "recommendation_en": audit.get("recommendation_en"),
    }


async def build_ma_intelligence_report(*, symbol: str = "BTC") -> dict[str, Any]:
    """
    M&A Intelligence surface — merger spreads + acquisition comps + deal readiness.
    """
    spread = await _token_merger_spread_signals(symbol)
    comps = await _acquisition_comps()
    catalog_hits: list[dict[str, Any]] = []
    try:
        from arbitrage_catalog import ARBITRAGE_CATALOG

        for row in ARBITRAGE_CATALOG:
            name = str(row.get("name", "")).lower()
            if "merger" in name or "m&a" in name or "acquisition" in name:
                catalog_hits.append(
                    {
                        "catalog_id": row.get("id"),
                        "name": row.get("name"),
                        "status": row.get("status"),
                        "active": row.get("active"),
                    }
                )
    except Exception:
        logger.debug("arbitrage_catalog unavailable for M&A cross-ref")

    readiness = "low"
    if spread["signal"] in {"elevated", "actionable"} and comps.get("strong_pillars", 0) >= 2:
        readiness = "high"
    elif spread["signal"] != "none" or comps.get("strong_pillars", 0) >= 1:
        readiness = "medium"

    return {
        "feature_ref": "ma_intelligence#113",
        "capability_id": 113,
        "symbol": symbol.upper(),
        "generated_at": _utcnow(),
        "readiness": readiness,
        "merger_spread": spread,
        "acquisition_comps": comps,
        "catalog_cross_refs": catalog_hits,
        "disclaimer": "Analytics only — not investment advice or M&A recommendation.",
        "no_execution": True,
        "ok": True,
    }
