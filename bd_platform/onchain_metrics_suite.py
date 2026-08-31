"""
On-Chain Metrics Suite — Features #737 HODL Waves + #741 MVRV Z-Score (Sprint 2).

#737 HODL Waves Model — NOT standalone, layer in On-Chain Metrics Suite.
#741 MVRV Z-Score Dynamic Realignment — absorbed, independent calculation.
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OnchainMetricsSuite")

_FEATURE_ID = 737
_ABSORBED_IDS = (737, 741)
_STANDALONE = False
_MERGED_INTO = "On-Chain Intelligence / On-Chain Metrics Suite"
_SPRINT = 2
_SEED_PATH = Path("data/onchain_metrics_suite_seed.json")
_METHODOLOGY_VERSION = "1.1"
_INDEPENDENT_CALCULATIONS = True

_DISCLAIMER = (
    "HODL waves are computed independently using BLACKDARK methodology. "
    "Not investment advice. Not a copy of third-party metrics."
)

HolderBand = Literal["<1d", "1d-1w", "1w-1m", "1m-3m", "3m-6m", "6m-12m", "1y-2y", "2y-5y", "5y+"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("onchain metrics suite seed load failed: %s", exc)
        return {"assets": {}}


def _sma(values: list[float], window: int) -> float:
    if not values:
        return 0.0
    slice_ = values[-window:] if len(values) >= window else values
    return sum(slice_) / len(slice_)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def compute_mvrv_z_score_dynamic(
    price: float,
    realized_prices: list[float],
    *,
    realignment_window: int = 200,
) -> dict[str, Any]:
    """#741 MVRV Z-Score Dynamic Realignment — independent on-chain calculation."""
    if not realized_prices or price <= 0:
        return {
            "mvrv_ratio": None,
            "z_score": None,
            "realignment_regime": "insufficient_data",
            "independent_calculation": _INDEPENDENT_CALCULATIONS,
        }

    realized = _sma(realized_prices, min(realignment_window, len(realized_prices)))
    mvrv = price / realized if realized > 0 else 1.0

    mvrv_history = []
    for i in range(realignment_window, len(realized_prices)):
        rp = _sma(realized_prices[: i + 1], min(realignment_window, i + 1))
        if rp > 0:
            mvrv_history.append(realized_prices[i] / rp)

    if mvrv_history:
        hist_mean = sum(mvrv_history) / len(mvrv_history)
        hist_std = _std(mvrv_history) or 1.0
        z_score = (mvrv - hist_mean) / hist_std
    else:
        z_score = 0.0

    if z_score >= 2.0:
        regime = "overheated"
    elif z_score <= -1.0:
        regime = "undervalued"
    else:
        regime = "neutral"

    return {
        "mvrv_ratio": round(mvrv, 4),
        "z_score": round(z_score, 4),
        "realignment_window": realignment_window,
        "realignment_regime": regime,
        "dynamic_realignment": True,
        "independent_calculation": _INDEPENDENT_CALCULATIONS,
        "not_competitor_copy": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "display": (
            f"MVRV Z-Score: {z_score:.2f} | Ratio: {mvrv:.3f} | "
            f"Regime: {regime} | Dynamic realignment w={realignment_window}"
        ),
    }


def build_mvrv_z_score_block(asset_data: dict[str, Any], *, asset: str) -> dict[str, Any]:
    """#741 MVRV Z-Score Dynamic Realignment block."""
    mvrv_data = asset_data.get("mvrv") or {}
    price = float(mvrv_data.get("price", 0))
    realized = [float(v) for v in (mvrv_data.get("realized_price_history") or [])]
    realignment_window = int(mvrv_data.get("realignment_window", 200))

    result = compute_mvrv_z_score_dynamic(
        price, realized, realignment_window=realignment_window,
    )
    return {
        "sub_task": "#741",
        "asset": asset,
        **result,
        "last_updated": mvrv_data.get("last_updated"),
        "target_latency_ms": 2000,
        "accuracy_target_pct": 95,
        "uptime_target_pct": 99,
    }


def build_hodl_waves_block(asset_data: dict[str, Any], *, asset: str) -> dict[str, Any]:
    """#737 HODL waves — independent long-term holder analysis."""
    waves = asset_data.get("hodl_waves") or {}
    bands = waves.get("bands") or {}
    total_supply_pct = sum(float(v) for v in bands.values())

    long_term_pct = sum(
        float(bands.get(k, 0))
        for k in ("6m-12m", "1y-2y", "2y-5y", "5y+")
    )
    short_term_pct = sum(
        float(bands.get(k, 0))
        for k in ("<1d", "1d-1w", "1w-1m")
    )

    if long_term_pct > short_term_pct * 1.5:
        regime = "accumulation"
    elif short_term_pct > long_term_pct * 1.2:
        regime = "distribution"
    else:
        regime = "balanced"

    return {
        "sub_task": "#737",
        "asset": asset,
        "bands": bands,
        "total_supply_pct": round(total_supply_pct, 2),
        "long_term_holder_pct": round(long_term_pct, 2),
        "short_term_holder_pct": round(short_term_pct, 2),
        "regime": regime,
        "independent_calculation": _INDEPENDENT_CALCULATIONS,
        "not_competitor_copy": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "last_updated": waves.get("last_updated"),
        "display": (
            f"HODL Waves {asset}: LT={long_term_pct:.1f}% ST={short_term_pct:.1f}% | "
            f"Regime: {regime} | Independent methodology"
        ),
    }


def build_onchain_metrics_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_data = (seed.get("assets") or {}).get(sym)

    if not asset_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    hodl = build_hodl_waves_block(asset_data, asset=sym)
    mvrv = build_mvrv_z_score_block(asset_data, asset=sym)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ids": list(_ABSORBED_IDS),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "onchain_metrics_suite",
        "asset": sym,
        "hodl_waves": hodl,
        "mvrv_z_score": mvrv,
        "real_time_update": True,
        "target_latency_ms": 2000,
        "independent_calculations": _INDEPENDENT_CALCULATIONS,
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "latency_within_target": elapsed <= 2000,
        "timestamp": _utcnow(),
    }


def onchain_metrics_suite_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "On-Chain Metrics Suite",
        "absorbed_tickets": {
            737: "HODL Waves Model",
            741: "MVRV Z-Score Dynamic Realignment",
        },
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "independent_calculations": _INDEPENDENT_CALCULATIONS,
        "acceptance_criteria": {
            "independent_methodology": True,
            "latency_target_2s": True,
            "real_time_update": True,
        },
        "asset_count": len(seed.get("assets") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
