"""
Options Context Module — Feature #744 (Sprint 2).

Max Pain / Gamma context for BTC/ETH. NOT a signal — context only.
No causal guarantee. Formula/version explicit.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.OptionsContext")

_FEATURE_ID = 744
_SPRINT = 2
_SEED_PATH = Path("data/options_context_seed.json")
_METHODOLOGY_VERSION = "1.1"
_FORMULA_SOURCE = "Deribit OI"

_NO_CAUSAL_DISCLAIMER = (
    "Max Pain is not a prediction. It is a snapshot of option positioning."
)

_LIMITATIONS = {
    "coverage": ["BTC", "ETH"],
    "excludes": ["CME options"],
    "update_frequency": "daily",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("options context seed load failed: %s", exc)
        return {"assets": {}}


def compute_max_pain(strikes: list[dict[str, Any]]) -> dict[str, Any]:
    """Max pain = strike minimizing total option holder loss at expiry."""
    if not strikes:
        return {"max_pain_strike": None, "method": "oi_weighted_pain_minimization"}

    pain_by_strike: dict[float, float] = {}
    for row in strikes:
        strike = float(row.get("strike", 0))
        call_oi = float(row.get("call_oi", 0))
        put_oi = float(row.get("put_oi", 0))
        for s in {float(r.get("strike", 0)) for r in strikes}:
            call_pain = max(0, s - strike) * call_oi
            put_pain = max(0, strike - s) * put_oi
            pain_by_strike[s] = pain_by_strike.get(s, 0) + call_pain + put_pain

    max_pain_strike = min(pain_by_strike, key=pain_by_strike.get) if pain_by_strike else None
    return {
        "max_pain_strike": max_pain_strike,
        "method": "oi_weighted_pain_minimization",
        "formula_version": _METHODOLOGY_VERSION,
        "source": _FORMULA_SOURCE,
    }


def compute_gamma_proxy(strikes: list[dict[str, Any]], spot: float) -> dict[str, Any]:
    """Gamma proxy from OI concentration near spot."""
    if not strikes or spot <= 0:
        return {"gamma_proxy": None, "concentration_near_spot": None}

    near_band = spot * 0.05
    near_oi = sum(
        float(r.get("call_oi", 0)) + float(r.get("put_oi", 0))
        for r in strikes
        if abs(float(r.get("strike", 0)) - spot) <= near_band
    )
    total_oi = sum(float(r.get("call_oi", 0)) + float(r.get("put_oi", 0)) for r in strikes)
    concentration = near_oi / total_oi if total_oi > 0 else 0

    if concentration >= 0.4:
        quality = "high"
    elif concentration >= 0.2:
        quality = "medium"
    else:
        quality = "low"

    return {
        "gamma_proxy": round(concentration, 4),
        "concentration_near_spot": round(concentration, 4),
        "data_quality": quality,
        "method": "oi_concentration_near_spot",
    }


def build_options_context_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()

    if sym not in _LIMITATIONS["coverage"]:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "asset_not_covered",
            "asset": sym,
            "coverage": _LIMITATIONS["coverage"],
        }

    asset_data = (seed.get("assets") or {}).get(sym)
    if not asset_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    strikes = asset_data.get("strikes") or []
    spot = float(asset_data.get("spot", 0))
    max_pain = compute_max_pain(strikes)
    gamma = compute_gamma_proxy(strikes, spot)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sprint": _SPRINT,
        "asset": sym,
        "spot": spot,
        "max_pain": max_pain,
        "gamma_context": gamma,
        "context_not_signal": True,
        "not_a_recommendation": True,
        "no_causal_guarantee": True,
        "no_causal_disclaimer": _NO_CAUSAL_DISCLAIMER,
        "disclaimer_hideable": False,
        "formula_version_display": (
            f"Max Pain calculated using {_FORMULA_SOURCE} | Methodology v{_METHODOLOGY_VERSION}"
        ),
        "limitations": {
            **_LIMITATIONS,
            "display": (
                f"Coverage: {'/'.join(_LIMITATIONS['coverage'])} only | "
                f"Excludes: {', '.join(_LIMITATIONS['excludes'])} | "
                f"Update: {_LIMITATIONS['update_frequency'].title()}"
            ),
        },
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def options_context_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Options Context Module",
        "sprint": _SPRINT,
        "coverage": _LIMITATIONS["coverage"],
        "formula_source": _FORMULA_SOURCE,
        "methodology_version": _METHODOLOGY_VERSION,
        "asset_count": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "no_causal_guarantee": True,
            "formula_version_explicit": True,
            "limitations_visible": True,
            "context_not_signal": True,
            "confidence_data_quality": True,
        },
        "no_causal_disclaimer": _NO_CAUSAL_DISCLAIMER,
        "timestamp": _utcnow(),
    }
