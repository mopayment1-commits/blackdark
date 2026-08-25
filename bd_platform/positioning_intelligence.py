"""
Positioning Intelligence Module — Feature #221 merged into Sentiment Panel (Sprint 2).

Top Trader Positioning — NOT copy-trade recommendations.
Provider semantics + source visible. Divergence alerts + cross-venue aggregation.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.PositioningIntelligence")

_FEATURE_ID = 221
_MERGED_INTO = "Sentiment Panel"
_STANDALONE = False
_SPRINT = 2
_SEED_PATH = Path("data/positioning_intelligence_seed.json")
_DISCLAIMER = (
    "Top trader data represents a subset of market participants. "
    "Past positioning does not predict future performance."
)

DivergenceLevel = Literal["low", "medium", "high"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"providers": {}, "assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("positioning intelligence seed load failed: %s", exc)
        return {"providers": {}, "assets": {}}


def _provider_display(provider_key: str, provider: dict[str, Any]) -> str:
    return (
        f"Source: {provider.get('name', provider_key)} | "
        f"Definition: {provider.get('definition', '')} | "
        f"Updated: {provider.get('update_cadence', 'hourly')}"
    )


def _classify_divergence(top_pct: float, retail_pct: float) -> DivergenceLevel:
    gap = abs(top_pct - retail_pct)
    if gap >= 35:
        return "high"
    if gap >= 20:
        return "medium"
    return "low"


def get_top_trader_positioning(asset: str = "BTC") -> dict[str, Any]:
    """Top-trader positioning panel — ratios only, NOT copy-trade signals."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)
    providers = seed.get("providers") or {}

    if not asset_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_configured", "asset": sym}

    venues: list[dict[str, Any]] = []
    weighted_top = 0.0
    weighted_global = 0.0
    total_weight = 0.0

    for venue_key, venue_data in (asset_data.get("venues") or {}).items():
        provider = providers.get(venue_key, {})
        top_long = float(venue_data.get("top_long_ratio_pct") or 0)
        global_long = float(venue_data.get("global_long_ratio_pct") or 0)
        weight = float(venue_data.get("volume_weight") or 0)
        weighted_top += top_long * weight
        weighted_global += global_long * weight
        total_weight += weight

        venues.append({
            "venue": venue_key,
            "provider_semantics": _provider_display(venue_key, provider),
            "top_trader_long_ratio_pct": top_long,
            "global_long_ratio_pct": global_long,
            "positioning_display": f"Top Trader Long Ratio: {top_long}%",
            "not_copy_trade": True,
            "source_visible": True,
        })

    agg_top = round(weighted_top / total_weight, 1) if total_weight else 0.0
    agg_global = round(weighted_global / total_weight, 1) if total_weight else 0.0
    retail = float(asset_data.get("retail_long_ratio_pct") or 0)
    divergence = _classify_divergence(agg_top, retail)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "surface": "top_trader_positioning_panel",
        "asset": sym,
        "aggregated_top_long_ratio_pct": agg_top,
        "aggregated_global_long_ratio_pct": agg_global,
        "retail_long_ratio_pct": retail,
        "cross_venue_display": (
            f"Aggregated across {len(venues)} exchanges | Weighted by volume"
        ),
        "venue_count": len(venues),
        "venues": venues,
        "divergence": {
            "level": divergence,
            "top_traders_long_pct": agg_top,
            "retail_long_pct": retail,
            "divergence_display": (
                f"Top Traders: {agg_top:.0f}% Long | Retail: {retail:.0f}% Long | "
                f"Divergence: {divergence.title()}"
            ),
        },
        "panel_display": f"Top Trader Long Ratio: {agg_top}%",
        "not_copy_trade": True,
        "not_a_recommendation": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "sla_met": elapsed <= 2000,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def get_positioning_divergence(asset: str = "BTC") -> dict[str, Any]:
    positioning = get_top_trader_positioning(asset)
    if not positioning.get("ok"):
        return positioning
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": positioning["asset"],
        "divergence": positioning["divergence"],
        "alert": positioning["divergence"]["level"] in ("medium", "high"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def positioning_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "module": "Positioning Intelligence Module",
        "sprint": _SPRINT,
        "provider_semantics_visible": True,
        "not_copy_trade": True,
        "cross_venue_aggregation": True,
        "divergence_alerts": True,
        "configured_assets": list((seed.get("assets") or {}).keys()),
        "venue_count": len(seed.get("providers") or {}),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
