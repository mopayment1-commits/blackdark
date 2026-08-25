"""
Technical Ratings — Feature #755 (Sprint 2).

Technical Composite including Momentum Intelligence (#273) as input.
Analysis layer — NOT standalone buy/sell recommendation.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.TechnicalRatings")

_FEATURE_ID = 755
_MERGED_FEATURES = (273,)
_STANDALONE = False
_SPRINT = 2

_DISCLAIMER = (
    "Technical ratings are composite analysis indicators. "
    "Not buy/sell signals. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def get_technical_composite(asset: str = "BTC") -> dict[str, Any]:
    """Technical Composite — momentum (#273) is a primary input, not standalone output."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")

    from bd_platform.momentum_intelligence import get_momentum_analysis

    momentum = get_momentum_analysis(sym)
    if not momentum.get("ok"):
        return momentum

    mom_score = float(momentum.get("momentum_score") or 5.0)
    windows = momentum.get("windows") or {}
    short_score = (windows.get("short") or {}).get("composite_score", mom_score)
    medium_score = (windows.get("medium") or {}).get("composite_score", mom_score)
    long_score = (windows.get("long") or {}).get("composite_score", mom_score)

    # Composite: weighted blend of momentum windows (momentum = 60% of technical composite)
    momentum_blend = round(short_score * 0.25 + medium_score * 0.45 + long_score * 0.30, 1)
    # Placeholder slots for future technical inputs (RSI, MA cross, etc.)
    technical_composite = round(momentum_blend * 0.60 + mom_score * 0.40, 1)

    if technical_composite >= 7.5:
        rating_label = "Strong"
    elif technical_composite >= 5.5:
        rating_label = "Neutral"
    else:
        rating_label = "Weak"

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "asset": sym,
        "technical_composite_score": technical_composite,
        "rating_label": rating_label,
        "rating_display": f"Technical Composite: {rating_label} ({technical_composite}/10)",
        "momentum_intelligence": momentum,
        "momentum_input_weight_pct": 60,
        "inputs": {
            "momentum_273": {
                "feature_id": 273,
                "score": mom_score,
                "weight_in_composite_pct": 60,
                "analysis_display": momentum.get("analysis_display"),
            },
        },
        "not_a_signal": True,
        "not_buy_sell": True,
        "not_standalone_recommendation": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "integrated_features": ["#273"],
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def technical_ratings_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "module": "Technical Ratings",
        "sprint": _SPRINT,
        "merged_features": list(_MERGED_FEATURES),
        "momentum_intelligence": "#273 merged as primary input",
        "not_a_signal": True,
        "not_standalone_recommendation": True,
        "surface": "Market Radar + Portfolio AI",
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
