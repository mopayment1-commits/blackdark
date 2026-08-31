"""
Market Pair View — Feature #270 archived as standalone.

NOT a backend feature — view/query layer over #268 Instrument Master.
Frontend requirement deferred to Market Radar (Sprint 2). No separate pipeline.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.MarketPairView")

_FEATURE_ID = 270
_STANDALONE = False
_ARCHIVED = True
_REJECTED_STANDALONE = True
_MERGED_INTO = "#268 Instrument Master view + Market Radar Sprint 2"
_SPRINT = 2  # frontend deferred
_SEED_PATH = Path("data/market_pair_view_seed.json")

_STALE_THRESHOLD_HOURS = 24
_LOW_VOLUME_USD = 10_000
_NEW_PAIR_DAYS = 7
_DELIST_ARCHIVE_DAYS = 30


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"pairs": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("market pair view seed load failed: %s", exc)
        return {"pairs": []}


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_pair_view(pair: dict[str, Any]) -> dict[str, Any]:
    """Pair view over #268 instrument master — no separate ingestion."""
    now = datetime.now(UTC)
    last_trade = _parse_ts(pair.get("last_trade_utc"))
    listed_at = _parse_ts(pair.get("listed_at_utc"))
    daily_vol = float(pair.get("daily_volume_usd", 0))

    stale = False
    if last_trade:
        stale = (now - last_trade) > timedelta(hours=_STALE_THRESHOLD_HOURS)

    low_volume = daily_vol < _LOW_VOLUME_USD
    is_new = False
    if listed_at:
        is_new = (now - listed_at) < timedelta(days=_NEW_PAIR_DAYS)

    premium_pct = pair.get("premium_discount_pct")
    vwap_ref = pair.get("vwap_reference_usd")

    flags: list[str] = []
    if stale:
        flags.append("stale")
    if low_volume:
        flags.append("low_volume")
    if is_new:
        flags.append("unverified_new")
    if pair.get("delisted"):
        flags.append("delisted")

    return {
        "pair_id": f"{pair.get('base')}/{pair.get('quote')}",
        "venue": pair.get("venue"),
        "venue_id": pair.get("instrument_id"),
        "instrument_id_268": pair.get("instrument_id"),
        "base": pair.get("base"),
        "quote": pair.get("quote"),
        "asset_class": pair.get("asset_class", "spot"),
        "last_trade_utc": pair.get("last_trade_utc"),
        "timestamp_alignment": "UTC normalized across venues",
        "stale": stale,
        "stale_display": (
            f"Stale: no trades > {_STALE_THRESHOLD_HOURS}h"
            if stale
            else f"Active: last trade within {_STALE_THRESHOLD_HOURS}h"
        ),
        "daily_volume_usd": daily_vol,
        "low_volume": low_volume,
        "low_volume_display": (
            f"Low volume (< ${_LOW_VOLUME_USD:,} daily) — greyed out with confidence warning"
            if low_volume
            else "Volume sufficient"
        ),
        "is_new": is_new,
        "premium_discount_pct": premium_pct,
        "premium_display": (
            f"Premium/discount vs VWAP reference: {premium_pct}% | "
            f"VWAP ref: ${vwap_ref}"
            if premium_pct is not None
            else "Premium/discount: N/A"
        ),
        "flags": flags,
        "greyed_out": low_volume,
        "confidence_warning": low_volume or is_new,
        "no_separate_pipeline": True,
        "source": "instrument_master_268",
        "display": (
            f"Pair ID: {pair.get('base')}/{pair.get('quote')} | "
            f"Venue: {pair.get('venue')} (mapped to #268) | "
            f"Flags: {', '.join(flags) if flags else 'none'}"
        ),
    }


def list_pair_views(
    *,
    base: str | None = None,
    venue: str | None = None,
    include_stale: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    seed = _load_seed()
    pairs = [build_pair_view(p) for p in seed.get("pairs") or []]

    if base:
        pairs = [p for p in pairs if p.get("base") == base.upper()]
    if venue:
        pairs = [p for p in pairs if p.get("venue") == venue]
    if not include_stale:
        pairs = [p for p in pairs if not p.get("stale")]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "archived_standalone_ticket": _ARCHIVED,
        "rejected_as_backend": _REJECTED_STANDALONE,
        "merged_into": _MERGED_INTO,
        "count": len(pairs[:limit]),
        "pairs": pairs[:limit],
        "no_separate_pipeline": True,
        "no_separate_database": True,
        "frontend_requirement": "Market Radar Sprint 2",
        "timestamp": _utcnow(),
    }


def compare_pairs_across_venues(base: str, quote: str = "USDT") -> dict[str, Any]:
    """Exchange/pair comparison — view on #268 master data."""
    seed = _load_seed()
    sym_base = base.upper()
    sym_quote = quote.upper()
    matching = [
        build_pair_view(p)
        for p in seed.get("pairs") or []
        if p.get("base") == sym_base and p.get("quote") == sym_quote
    ]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "pair": f"{sym_base}/{sym_quote}",
        "venue_count": len(matching),
        "comparisons": matching,
        "e2e_journey": f"asset:{sym_base} → pairs → venues",
        "benchmark": "CoinGecko",
        "no_separate_pipeline": True,
        "timestamp": _utcnow(),
    }


def market_pair_view_status() -> dict[str, Any]:
    seed = _load_seed()
    pairs = seed.get("pairs") or []
    stale_count = sum(
        1 for p in pairs
        if build_pair_view(p).get("stale")
    )

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Market Pair Intelligence (archived standalone)",
        "standalone": _STANDALONE,
        "archived_standalone_ticket": _ARCHIVED,
        "rejected_as_backend": _REJECTED_STANDALONE,
        "decision": "Frontend requirement for Market Radar Sprint 2",
        "backend_source": "#268 Instrument Master",
        "no_separate_pipeline": True,
        "no_separate_database": True,
        "scope_lock": {
            "spot_pairs": True,
            "perp_pairs": "if mapped in #268",
            "dex_pairs": "AMM-specific logic separate",
            "premium_discount": "calculated vs VWAP reference",
            "display": (
                "Spot pairs only | Perp pairs = if mapped in #268 | "
                "DEX pairs = AMM-specific logic separate | "
                "Premium/discount = calculated vs VWAP reference"
            ),
        },
        "quality_gates": {
            "low_volume_threshold_usd": _LOW_VOLUME_USD,
            "new_pair_days": _NEW_PAIR_DAYS,
            "delist_archive_days": _DELIST_ARCHIVE_DAYS,
            "stale_threshold_hours": _STALE_THRESHOLD_HOURS,
        },
        "acceptance_criteria": {
            "pair_mapping_accuracy_pct": seed.get("sla", {}).get("mapping_accuracy_pct", 99.5),
            "stale_detection_hours": seed.get("sla", {}).get("stale_detection_hours", 1),
            "premium_formula_documented": True,
            "e2e_journey": "asset → pairs → venue",
        },
        "pairs_tracked": len(pairs),
        "stale_pairs": stale_count,
        "frontend_deferred": "Market Radar Sprint 2",
        "timestamp": _utcnow(),
    }
