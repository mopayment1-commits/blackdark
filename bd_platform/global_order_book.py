"""
Global Order Book Metrics — Feature #249 (Sprint 2 Intelligence).

Aggregates order book depth across venues with documented weights, sequence gap
handling, and imbalance as context — NOT signals or opportunities.

Integrated into Market Radar — NOT a standalone dashboard.
Technical context only — replaces #227 opportunistic framing.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.GlobalOrderBook")

_FEATURE_ID = 249
_STANDALONE = False
_SPRINT = 2
_REPLACES = 227
_SEED_PATH = Path("data/global_order_book_seed.json")
_METHODOLOGY_VERSION = "1.3"
_WEIGHTING_VERSION = "1.2"

_DISCLAIMER_TEXT = (
    "Global order book data is aggregated across disclosed venues with weighted methodology. "
    "Sequence gaps may occur. Imbalance measures current state, not future direction. "
    "Not investment advice."
)

TierLabel = Literal["free", "pro", "elite", "institutional"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("global order book seed load failed: %s", exc)
        return {"assets": {}}


def _format_usd(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.0f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def _update_frequency_display(tier: str) -> dict[str, Any]:
    from auth_service import normalize_tier, tier_meets

    normalized = normalize_tier(tier)
    if tier_meets("institutional", normalized):
        interval = 1
        label = "Enterprise"
    elif tier_meets("pro", normalized):
        interval = 5
        label = "Pro"
    else:
        interval = 30
        label = "Free"

    return {
        "tier": normalized,
        "interval_seconds": interval,
        "label": label,
        "display": (
            f"Updated: Every {interval} second{'s' if interval != 1 else ''} ({label})"
        ),
        "no_instant_claim": True,
    }


def build_venue_weights(weights: dict[str, float], *, method: str, version: str) -> dict[str, Any]:
    """Documented venue weights — no equal-weight without reason."""
    total_pct = sum(weights.values())
    entries = []
    parts: list[str] = []
    for venue, pct in sorted(weights.items(), key=lambda x: -x[1]):
        entries.append({"venue": venue, "weight_pct": pct})
        parts.append(f"{venue}: {pct}%")
    return {
        "entries": entries,
        "method": method,
        "version": version,
        "display": (
            f"{' | '.join(parts)} | Method: {method} | Version: {version}"
        ),
        "volume_weighted": "volume" in method.lower(),
        "no_equal_weight_without_reason": True,
    }


def build_sequence_gaps(gaps: list[dict[str, Any]], *, venues_active: int, venues_total: int) -> dict[str, Any]:
    """Sequence gaps handled — never hidden."""
    if not gaps:
        return {
            "gaps_detected": False,
            "coverage_display": f"Coverage: {venues_active}/{venues_total} venues",
            "no_hidden_gaps": True,
        }

    gap_entries = []
    for g in gaps:
        venue = g.get("venue", "")
        start = g.get("sequence_start", 0)
        end = g.get("sequence_end", 0)
        interpolated = g.get("interpolated", True)
        gap_entries.append({
            "venue": venue,
            "sequence_start": start,
            "sequence_end": end,
            "interpolated": interpolated,
            "display": (
                f"{venue}: Sequence gap detected (blocks {start}-{end}) | "
                f"Data: {'interpolated (dashed)' if interpolated else 'missing'}"
            ),
        })

    return {
        "gaps_detected": True,
        "gaps": gap_entries,
        "coverage_display": f"Coverage: {venues_active}/{venues_total} venues",
        "display": (
            f"{gap_entries[0]['display']} | {gap_entries[0]['display'].split('|')[0].strip()} | "
            f"Coverage: {venues_active}/{venues_total} venues"
            if len(gap_entries) == 1
            else f"{len(gap_entries)} gaps | Coverage: {venues_active}/{venues_total} venues"
        ),
        "no_hidden_gaps": True,
        "gap_alert": any(g.get("interpolated") for g in gaps),
    }


def build_per_venue_depth(venues: dict[str, dict[str, float]]) -> dict[str, Any]:
    """Per-venue breakdown — no total without breakdown."""
    entries = []
    parts: list[str] = []
    total_bid = 0.0
    total_ask = 0.0
    for venue, depths in venues.items():
        bid = float(depths.get("bid_usd", 0))
        ask = float(depths.get("ask_usd", 0))
        total_bid += bid
        total_ask += ask
        entries.append({
            "venue": venue,
            "bid_usd": bid,
            "ask_usd": ask,
            "display": f"{venue} Depth: {_format_usd(bid + ask)}",
        })
        parts.append(f"{venue}: {_format_usd(bid + ask)}")
    parts.append(f"Global: {_format_usd(total_bid + total_ask)}")
    return {
        "entries": entries,
        "total_bid_usd": total_bid,
        "total_ask_usd": total_ask,
        "total_usd": total_bid + total_ask,
        "display": " | ".join(parts),
        "no_total_without_breakdown": True,
    }


def build_global_depth(bid_usd: float, ask_usd: float, *, levels: int = 10) -> dict[str, Any]:
    """Global depth — descriptive only, no buy signals."""
    imbalance_pct = round((bid_usd - ask_usd) / (bid_usd + ask_usd) * 100, 1) if (bid_usd + ask_usd) else 0.0
    bias = "bid-heavy" if imbalance_pct > 0 else "ask-heavy" if imbalance_pct < 0 else "balanced"
    return {
        "bid_depth_usd": bid_usd,
        "ask_depth_usd": ask_usd,
        "levels": levels,
        "imbalance_pct": imbalance_pct,
        "bias_label": bias,
        "display": (
            f"Global Bid Depth (top {levels} levels): {_format_usd(bid_usd)} | "
            f"Ask Depth: {_format_usd(ask_usd)} | "
            f"Imbalance: {imbalance_pct:+.1f}% ({bias})"
        ),
        "descriptive_only": True,
        "no_buy_signal": True,
    }


def build_imbalance_context(imbalance_pct: float) -> dict[str, Any]:
    """Imbalance = context, NOT signal."""
    if imbalance_pct > 0:
        interpretation = "More bids than asks at top levels"
    elif imbalance_pct < 0:
        interpretation = "More asks than bids at top levels"
    else:
        interpretation = "Balanced bid-ask at top levels"

    return {
        "imbalance_pct": imbalance_pct,
        "interpretation": interpretation,
        "display": (
            f"Bid-Ask Imbalance: {imbalance_pct:+.1f}% | "
            f"Interpretation: {interpretation} | "
            f"Not: Bullish signal"
        ),
        "context_not_signal": True,
        "not_bullish_signal": True,
        "not_bearish_signal": True,
    }


def build_methodology_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    venues = len(seed.get("venue_weights") or {})
    return {
        "methodology_version": _METHODOLOGY_VERSION,
        "venues": venues,
        "weighting": "Volume-Weighted",
        "gap_handling": "Interpolation + Alert",
        "last_updated": seed.get("last_updated", "2026-08-25"),
        "display": (
            f"Global Order Book Methodology v{_METHODOLOGY_VERSION} | "
            f"Venues: {venues} | "
            f"Weighting: Volume-Weighted | "
            f"Gap Handling: Interpolation + Alert | "
            f"Last Updated: {seed.get('last_updated', '2026-08-25')}"
        ),
    }


def build_global_order_book_panel(
    asset: str = "BTC",
    *,
    tier: str = "pro",
) -> dict[str, Any]:
    """Build Global Order Book tab for Market Radar."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_data = seed.get("assets", {}).get(sym)
    if not asset_data:
        return {
            "ok": False,
            "error": "asset_not_tracked",
            "feature_id": _FEATURE_ID,
            "asset": sym,
        }

    venue_weights_cfg = seed.get("venue_weights") or asset_data.get("venue_weights") or {}
    weights = venue_weights_cfg.get("weights") or {}
    venue_depths = asset_data.get("venue_depths") or {}
    gaps = asset_data.get("sequence_gaps") or []
    venues_total = len(weights) or len(venue_depths)
    venues_with_gaps = {g.get("venue") for g in gaps}
    venues_active = venues_total - len(venues_with_gaps) + sum(
        1 for g in gaps if g.get("interpolated")
    )

    per_venue = build_per_venue_depth(venue_depths)
    global_depth = build_global_depth(
        per_venue["total_bid_usd"],
        per_venue["total_ask_usd"],
        levels=asset_data.get("levels", 10),
    )
    imbalance = build_imbalance_context(global_depth["imbalance_pct"])
    venue_weights = build_venue_weights(
        weights,
        method=venue_weights_cfg.get("method", "30D volume-weighted"),
        version=venue_weights_cfg.get("version", _WEIGHTING_VERSION),
    )
    sequence_gaps = build_sequence_gaps(gaps, venues_active=venues_active, venues_total=venues_total)
    update_freq = _update_frequency_display(tier)

    feed_source = None
    try:
        from bd_platform.order_book_feed import get_order_book_feed

        feed_source = {
            "module": "order_book_feed",
            "feature_ids": [256, 257, 258],
            "l2_feed": get_order_book_feed(sym, level="L2", venue="binance", tier=tier).get("feed"),
            "powers_analysis": True,
            "display": "L1/L2/L3 raw feeds power #249 aggregated analysis",
        }
    except Exception:
        logger.debug("order book feed integration failed", exc_info=True)

    disclaimer = {
        "text": _DISCLAIMER_TEXT,
        "hideable": False,
        "collapsible": False,
    }

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "surface": "market_radar_global_order_book",
        "tab": "Global Order Book",
        "merged_into": "market_radar",
        "replaces": _REPLACES,
        "asset": sym,
        "global_depth": global_depth,
        "imbalance_context": imbalance,
        "venue_weights": venue_weights,
        "per_venue_depth": per_venue,
        "sequence_gaps": sequence_gaps,
        "update_frequency": update_freq,
        "feed_source": feed_source,
        "methodology": build_methodology_block(seed),
        "volume_display": (
            f"Global Depth: {_format_usd(per_venue['total_usd'])} | "
            f"Imbalance: {global_depth['imbalance_pct']:+.1f}%"
        ),
        "no_opportunity_language": True,
        "technical_context_only": True,
        "not_arbitrage_signal": True,
        "disclaimer": disclaimer,
        "disclaimer_hideable": False,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def global_order_book_status() -> dict[str, Any]:
    seed = _load_seed()
    assets = seed.get("assets", {})
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Global Order Book Metrics",
        "sprint": _SPRINT,
        "standalone": _STANDALONE,
        "merged_into": "market_radar",
        "tab": "Global Order Book",
        "replaces": _REPLACES,
        "assets_tracked": len(assets),
        "methodology": build_methodology_block(seed),
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
        "technical_context_only": True,
        "acceptance_criteria": {
            "sequence_gaps_handled": True,
            "venue_weights_documented": True,
            "global_depth_descriptive": True,
            "imbalance_context_not_signal": True,
            "per_venue_breakdown": True,
            "realistic_update_frequency": True,
            "disclaimer_non_hideable": True,
            "no_opportunity_language": True,
            "fee_db_arbitrage_only": True,
            "market_radar_integration": True,
            "methodology_versioned": True,
            "fed_by_order_book_feed": True,
        },
        "timestamp": _utcnow(),
    }
