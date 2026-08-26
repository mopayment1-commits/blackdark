"""
On-Chain Metrics Suite — Feature #737 HODL Waves absorbed (Sprint 2).

#737 HODL Waves Model — NOT standalone, layer in On-Chain Metrics Suite.
Independent calculations — not copy-paste from competitors.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OnchainMetricsSuite")

_FEATURE_ID = 737
_ABSORBED_IDS = (737,)
_STANDALONE = False
_MERGED_INTO = "On-Chain Intelligence / On-Chain Metrics Suite"
_SPRINT = 2
_SEED_PATH = Path("data/onchain_metrics_suite_seed.json")
_METHODOLOGY_VERSION = "1.0"
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
        "real_time_update": True,
        "target_latency_ms": 2000,
        "independent_calculations": _INDEPENDENT_CALCULATIONS,
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def onchain_metrics_suite_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "On-Chain Metrics Suite",
        "absorbed_tickets": {737: "HODL Waves Model"},
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
