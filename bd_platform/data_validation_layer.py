"""
Data Validation Layer — Feature #147 (Sprint 0, with #133).

Internal protection — NOT a user-facing feature.
Automatic: outlier >5% from weighted reference → flag → fallback source → log event.

User-visible surface only:
  ✓ Price Verified badge
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.unified_connector_layer import CanonicalPriceQuote

logger = logging.getLogger("BLACKDARK.DataValidation")

_FEATURE_ID = 147
_EVENTS_PATH = Path("data/data_validation_events.jsonl")
_OUTLIER_THRESHOLD_PCT = 5.0  # institutional: >5% from reference = flag


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append_event(row: dict[str, Any]) -> None:
    _EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _EVENTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _reference_price(quotes: list[CanonicalPriceQuote]) -> float:
    """Volume-weighted reference; median fallback."""
    if not quotes:
        return 0.0
    total_vol = sum(max(q.volume_24h_usd, 1.0) for q in quotes)
    if total_vol > len(quotes):
        return sum(q.price_usd * max(q.volume_24h_usd, 1.0) for q in quotes) / total_vol
    prices = [q.price_usd for q in quotes if q.price_usd > 0]
    return statistics.median(prices) if prices else 0.0


def _select_fallback(quotes: list[CanonicalPriceQuote], reference: float) -> CanonicalPriceQuote | None:
    """Pick best fallback: live WS first, then closest to reference with volume."""
    if not quotes or reference <= 0:
        return None

    live = [q for q in quotes if q.connector_id.startswith("ws_") and q.price_usd > 0]
    pool = live or quotes

    def score(q: CanonicalPriceQuote) -> tuple[float, float]:
        deviation = abs(q.price_usd - reference) / reference
        return (deviation, -max(q.volume_24h_usd, 0))

    return min(pool, key=score)


def validate_quotes(
    quotes: list[CanonicalPriceQuote],
    *,
    asset: str,
    context: str = "price_aggregation",
) -> dict[str, Any]:
    """
    #147 — validate prices, flag outliers, select fallback, log events.

    Returns validation block with user badge only when verified.
    """
    t0 = time.perf_counter()
    if not quotes:
        elapsed = time.perf_counter() - t0
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "no_quotes",
            "price_verified": False,
            "user_badge": None,
            "sla_met": elapsed <= 2.0,
            "timestamp": _utcnow(),
        }

    reference = _reference_price(quotes)
    validated: list[CanonicalPriceQuote] = []
    flagged: list[dict[str, Any]] = []

    for q in quotes:
        if reference <= 0:
            validated.append(q)
            continue
        deviation_pct = abs(q.price_usd - reference) / reference * 100
        if deviation_pct > _OUTLIER_THRESHOLD_PCT and len(quotes) >= 2:
            event = {
                "feature_id": _FEATURE_ID,
                "event_type": "pricing_outlier_flagged",
                "asset": asset,
                "context": context,
                "connector_id": q.connector_id,
                "exchange": q.exchange,
                "price_usd": q.price_usd,
                "reference_usd": round(reference, 8),
                "deviation_pct": round(deviation_pct, 3),
                "action": "flag_and_fallback",
                "reason": "isolated_price_during_platform_update_or_api_glitch",
                "timestamp": _utcnow(),
            }
            flagged.append(event)
            _append_event(event)
            logger.warning(
                "Data validation flagged outlier | asset=%s connector=%s deviation=%.2f%%",
                asset,
                q.connector_id,
                deviation_pct,
            )
        else:
            validated.append(q)

    if not validated:
        fallback = _select_fallback(quotes, reference)
        if fallback:
            validated = [fallback]
            _append_event(
                {
                    "feature_id": _FEATURE_ID,
                    "event_type": "fallback_source_selected",
                    "asset": asset,
                    "context": context,
                    "fallback_connector": fallback.connector_id,
                    "fallback_price_usd": fallback.price_usd,
                    "reference_usd": round(reference, 8),
                    "timestamp": _utcnow(),
                }
            )

    verified = len(flagged) == 0 and len(validated) >= 1
    fallback_used = len(flagged) > 0 and len(validated) >= 1

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "mode": "data_validation_layer",
        "user_facing": False,
        "asset": asset,
        "reference_price_usd": round(reference, 8),
        "validated_quotes": validated,
        "flagged_count": len(flagged),
        "flagged_events": flagged,
        "fallback_used": fallback_used,
        "price_verified": verified or fallback_used,
        "user_badge": "✓ Price Verified" if (verified or fallback_used) else None,
        "user_badge_ar": "✓ السعر موثّق" if (verified or fallback_used) else None,
        "outlier_threshold_pct": _OUTLIER_THRESHOLD_PCT,
        "integrated_with": ["#133"],
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


def validation_layer_status() -> dict[str, Any]:
    event_count = 0
    if _EVENTS_PATH.exists():
        event_count = sum(1 for ln in _EVENTS_PATH.read_text(encoding="utf-8").splitlines() if ln.strip())

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "role": "data_validation_layer",
        "user_facing": False,
        "user_surface": "price_verified_badge_only",
        "outlier_threshold_pct": _OUTLIER_THRESHOLD_PCT,
        "pipeline": ["detect_outlier", "flag", "fallback_source", "log_event"],
        "events_logged": event_count,
        "integrated_with": ["#133"],
        "timestamp": _utcnow(),
    }
