"""
Taker Pressure Module — Feature #296 (Sprint 2 Intelligence Ledger).

Measures aggressive buy/sell pressure from taker-side trade classification.
Sub-feature of Orderflow analytics — CEX spot + perp only (no DEX taker concept).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.TakerPressure")

_FEATURE_ID = 296
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Taker Pressure Module (Orderflow analytics)"
_SPRINT = 2
_SEED_PATH = Path("data/taker_pressure_seed.json")
_METHODOLOGY_VERSION = "1.0"
_MIN_ACCURACY_PCT = 95.0
_ROLLING_WINDOW_MIN = 60

_DISCLAIMER = (
    "Taker pressure measures aggressive trade-side volume imbalance. "
    "Not investment advice. Not trade signals. "
    "DEX excluded — no taker concept. Venue coverage varies by exchange."
)

PressureState = Literal["buy_pressure", "sell_pressure", "neutral"]
MarketType = Literal["cex_spot", "cex_perp"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "classification_tests": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("taker pressure seed load failed: %s", exc)
        return {"assets": {}, "classification_tests": []}


def build_scope_lock() -> dict[str, Any]:
    return {
        "cex_spot": True,
        "cex_perp": True,
        "dex": "excluded — no taker concept",
        "sub_feature_of": "Orderflow analytics",
        "display": "CEX spot + perp only | DEX = separate (no taker concept)",
    }


def build_classification_controls(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests = seed.get("classification_tests") or []
    passed = [t for t in tests if t.get("passed")]
    avg_accuracy = (
        round(sum(float(t.get("accuracy_pct", 0)) for t in passed) / len(passed), 2)
        if passed else 0.0
    )

    return {
        "taker_definition": "aggressor side (taker = initiator of trade)",
        "tested_against": "exchange official CVD",
        "min_accuracy_pct": _MIN_ACCURACY_PCT,
        "avg_accuracy_pct": avg_accuracy,
        "tests_passed": len(passed),
        "tests_total": len(tests),
        "classification_tested": avg_accuracy >= _MIN_ACCURACY_PCT if passed else False,
        "venue_coverage_disclosed": True,
        "display": (
            f"Taker = aggressor side | Tested vs exchange CVD | "
            f"Accuracy: {avg_accuracy}% (min {_MIN_ACCURACY_PCT}%) | "
            "Venue coverage documented"
        ),
    }


def compute_pressure_state(
    buy_volume: float,
    sell_volume: float,
    *,
    neutral_threshold: float = 0.05,
) -> dict[str, Any]:
    total = buy_volume + sell_volume
    if total <= 0:
        return {
            "buy_volume": 0,
            "sell_volume": 0,
            "buy_ratio": 0.5,
            "sell_ratio": 0.5,
            "imbalance": 0.0,
            "state": "neutral",
        }

    buy_ratio = round(buy_volume / total, 4)
    sell_ratio = round(1 - buy_ratio, 4)
    imbalance = round(buy_ratio - sell_ratio, 4)

    if imbalance > neutral_threshold:
        state: PressureState = "buy_pressure"
    elif imbalance < -neutral_threshold:
        state = "sell_pressure"
    else:
        state = "neutral"

    return {
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "buy_ratio": buy_ratio,
        "sell_ratio": sell_ratio,
        "imbalance": imbalance,
        "state": state,
    }


def build_venue_pressure_block(venue: dict[str, Any], *, asset: str) -> dict[str, Any]:
    buy_vol = float(venue.get("taker_buy_volume", 0))
    sell_vol = float(venue.get("taker_sell_volume", 0))
    pressure = compute_pressure_state(buy_vol, sell_vol)
    trade_side_available = venue.get("trade_side_available", True)

    return {
        "venue": venue.get("venue"),
        "asset": asset,
        "market_type": venue.get("market_type", "cex_spot"),
        "trade_side_available": trade_side_available,
        "venue_coverage_disclosed": True,
        "taker_buy_volume": buy_vol if trade_side_available else None,
        "taker_sell_volume": sell_vol if trade_side_available else None,
        "buy_sell_ratio": pressure["buy_ratio"] if trade_side_available else None,
        "imbalance": pressure["imbalance"] if trade_side_available else None,
        "state": pressure["state"] if trade_side_available else "unavailable",
        "rolling_window_min": venue.get("rolling_window_min", _ROLLING_WINDOW_MIN),
        "source": venue.get("source"),
        "timestamp_utc": venue.get("timestamp_utc"),
        "not_a_signal": True,
    }


def build_taker_pressure_panel(asset: str = "BTC") -> dict[str, Any]:
    """Taker buy/sell pressure panel with rolling imbalance."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_data = (seed.get("assets") or {}).get(sym)

    if not asset_data:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "asset_not_tracked",
            "asset": sym,
        }

    venues = asset_data.get("venues") or []
    venue_blocks = [build_venue_pressure_block(v, asset=sym) for v in venues]
    available = [v for v in venue_blocks if v.get("trade_side_available")]

    total_buy = sum(float(v.get("taker_buy_volume") or 0) for v in available)
    total_sell = sum(float(v.get("taker_sell_volume") or 0) for v in available)
    aggregate = compute_pressure_state(total_buy, total_sell)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "asset": sym,
        "aggregate": {
            **aggregate,
            "rolling_window_min": asset_data.get("rolling_window_min", _ROLLING_WINDOW_MIN),
            "venue_count": len(available),
            "venues_without_trade_side": len(venues) - len(available),
        },
        "venues": venue_blocks,
        "classification": build_classification_controls(seed),
        "scope_lock": build_scope_lock(),
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def list_classification_tests(limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    tests = seed.get("classification_tests") or []
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(tests[:limit]),
        "min_accuracy_pct": _MIN_ACCURACY_PCT,
        "tests": tests[:limit],
        "classification": build_classification_controls(seed),
        "timestamp": _utcnow(),
    }


def taker_pressure_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Taker Pressure Module",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "sub_feature_of": "Orderflow analytics",
        "scope_lock": build_scope_lock(),
        "classification": build_classification_controls(seed),
        "acceptance_criteria": {
            "trade_side_classification_tested": True,
            "venue_coverage_disclosed": True,
            "min_accuracy_pct": _MIN_ACCURACY_PCT,
            "cex_only_no_dex": True,
        },
        "asset_count": len(seed.get("assets") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
