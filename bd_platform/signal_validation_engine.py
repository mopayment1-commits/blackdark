"""
Signal Validation Engine — Feature #747 merged (Sprint 2).

Multi-Timeframe Decision Convergence as validation layer inside Signal Engine.
NOT standalone — filter before signal trust, not a separate product surface.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.SignalValidation")

_FEATURE_ID = 747
_MERGED_INTO = "Signal Engine validation layer"
_STANDALONE = False
_SLA_MS = 2000

_REGIME_LABELS = {
    "convergent": "🟢 Convergent",
    "divergent": "🔴 Divergent",
    "flat": "🟡 Flat",
    "insufficient_data": "⚪ Insufficient data",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _classify_mtf_regime(confluence: dict[str, Any]) -> str:
    frames = confluence.get("frames") or {}
    biases = [f.get("bias") for f in frames.values() if f.get("bias") in {"bull", "bear", "flat"}]
    if not biases:
        return "insufficient_data"
    actionable = [b for b in biases if b != "flat"]
    if len(actionable) >= 2 and len(set(actionable)) == 1:
        return "convergent"
    if len(set(actionable)) > 1:
        return "divergent"
    return "flat"


async def validate_mtf_convergence(asset: str) -> dict[str, Any]:
    """#747 MTF Decision Convergence — validation filter, not standalone signal."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")

    try:
        from technical_analysis import compute_timeframe_confluence

        confluence = await compute_timeframe_confluence(sym)
    except Exception as exc:
        logger.debug("mtf confluence failed for %s: %s", sym, exc)
        confluence = {"aligned": None, "score_penalty": 5.0, "frames": {}, "error": str(exc)}

    regime = _classify_mtf_regime(confluence)
    aligned = confluence.get("aligned")
    penalty = float(confluence.get("score_penalty") or 0)
    validation_passed = aligned is True or (aligned is None and penalty < 5)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "surface": "mtf_validation_layer",
        "validation_passed": validation_passed,
        "mtf_regime": regime,
        "regime_display": _REGIME_LABELS.get(regime, regime),
        "aligned": aligned,
        "score_penalty": penalty,
        "frames": confluence.get("frames") or {},
        "convergence_display": (
            f"MTF {regime}: {'frames aligned' if aligned else 'frames disagree — filter active'}"
        ),
        "filter_role": "validation_layer",
        "not_a_prediction": True,
        "sla_met": elapsed_ms <= _SLA_MS,
        "latency_ms": elapsed_ms,
        "timestamp": _utcnow(),
    }


async def run_signal_validation(
    asset: str,
    *,
    opportunity_score: float | None = None,
) -> dict[str, Any]:
    """Full signal validation — MTF convergence + score gate."""
    t0 = time.perf_counter()
    mtf = await validate_mtf_convergence(asset)
    adjusted_score = opportunity_score
    if opportunity_score is not None:
        adjusted_score = max(0.0, min(100.0, opportunity_score - float(mtf.get("score_penalty") or 0)))

    signal_trusted = bool(mtf.get("validation_passed")) and (
        adjusted_score is None or adjusted_score >= 40
    )
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": asset.upper(),
        "signal_trusted": signal_trusted,
        "mtf_validation": mtf,
        "original_score": opportunity_score,
        "adjusted_score": adjusted_score,
        "validation_display": (
            f"Signal {'trusted' if signal_trusted else 'filtered'} — {mtf.get('regime_display')}"
        ),
        "filter_role": "validation_layer",
        "not_a_prediction": True,
        "sla_met": elapsed_ms <= _SLA_MS,
        "latency_ms": elapsed_ms,
        "timestamp": _utcnow(),
    }


def signal_validation_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "module": "Signal Validation Engine",
        "sprint": 2,
        "mtf_convergence": True,
        "filter_not_feature": True,
        "timeframes": ["15m", "1h", "4h"],
        "sla_response_ms": _SLA_MS,
        "not_a_prediction": True,
        "timestamp": _utcnow(),
    }
