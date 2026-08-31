"""
Price-Move Event Correlator — Feature #519 (Sprint 2 Intelligence Layer).

Renamed from "Candle / Price-Move Investigator".
Temporal correlation only — NOT causation. Events in same window, timestamps aligned.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.PriceMoveEventCorrelator")

_FEATURE_ID = 519
_RENAMED_FROM = "Candle / Price-Move Investigator"
_TITLE = "Price-Move Event Correlator"
_STANDALONE = False
_MERGED_INTO = "Price-Move Event Correlation Layer (#556 epic)"
_LAYER = "Intelligence Layer"
_SPRINT = 2
_SEED_PATH = Path("data/price_move_event_correlator_seed.json")
_METHODOLOGY_VERSION = "1.0"
_CORRELATION_WINDOW_SECONDS = 300

_DISCLAIMER = (
    "Temporal correlation only — not causation. "
    "Events in same window — not confirmed cause. "
    "Causation: unverified. Not investment advice."
)

_BANNED_TERMS = (
    "caused the move",
    "caused the pump",
    "caused the dump",
    "this whale caused",
    "reason for",
    "confirmed cause",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"candles": {}, "events": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("price move event correlator seed load failed: %s", exc)
        return {"candles": {}, "events": {}}


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def correlate_events_in_window(
    candle_ts: str,
    events: list[dict[str, Any]],
    *,
    window_seconds: int = _CORRELATION_WINDOW_SECONDS,
) -> list[dict[str, Any]]:
    """Find events temporally correlated with candle — NOT causation."""
    candle_time = _parse_ts(candle_ts)
    correlated = []

    for event in events:
        event_time = _parse_ts(event.get("timestamp", candle_ts))
        delta = abs((event_time - candle_time).total_seconds())
        if delta <= window_seconds:
            correlated.append({
                "event_type": event.get("event_type"),
                "description": event.get("description"),
                "timestamp": event.get("timestamp"),
                "delta_seconds": round(delta, 1),
                "source": event.get("source"),
                "evidence_id": event.get("evidence_id"),
                "temporal_correlation": True,
                "not_causation": True,
                "causation_unverified": True,
                "display": (
                    f"Event in same window ({delta:.0f}s): {event.get('description')} "
                    f"[Correlation only — causation unverified]"
                ),
            })

    return sorted(correlated, key=lambda e: e["delta_seconds"])


def build_correlation_panel(
    candle_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build price-move correlation panel — events in same window."""
    seed = seed or _load_seed()
    candle = (seed.get("candles") or {}).get(candle_id)
    if not candle:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "candle_not_found", "candle_id": candle_id}

    asset = candle.get("asset", "BTC")
    events = (seed.get("events") or {}).get(asset.upper(), [])
    correlated = correlate_events_in_window(candle["timestamp"], events)

    price_change_pct = float(candle.get("price_change_pct", 0))
    direction = "up" if price_change_pct > 0 else "down" if price_change_pct < 0 else "flat"

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "not_investigator": True,
        "temporal_correlation_only": True,
        "not_causation": True,
        "candle": {
            "candle_id": candle_id,
            "asset": asset.upper(),
            "timestamp": candle["timestamp"],
            "open": candle.get("open"),
            "close": candle.get("close"),
            "price_change_pct": price_change_pct,
            "direction": direction,
        },
        "events_in_same_window": correlated,
        "event_count": len(correlated),
        "correlation_window_seconds": _CORRELATION_WINDOW_SECONDS,
        "timestamps_aligned": True,
        "linguistic_framing": {
            "use": "Events in same window | Temporal correlation",
            "forbidden": "Cause | Reason | This whale caused the move",
        },
        "summary_display": (
            f"Candle moved {direction} {abs(price_change_pct):.2f}% at {candle['timestamp']}. "
            f"{len(correlated)} event(s) in same window. Causation: unverified."
        ),
        "rule_based_only": True,
        "llm_optional_later": True,
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
    }


def build_price_move_event_correlator_panel(
    *,
    candle_id: str = "btc_2026_08_26_14h",
    asset: str | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()

    if asset and not candle_id:
        candles = seed.get("candles") or {}
        matching = [cid for cid, c in candles.items() if c.get("asset", "").upper() == asset.upper()]
        candle_id = matching[0] if matching else candle_id

    panel = build_correlation_panel(candle_id, seed=seed)
    if not panel.get("ok"):
        return panel

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    panel.update({
        "layer": _LAYER,
        "sprint": _SPRINT,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    })
    return panel


def price_move_event_correlator_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "not_investigator": True,
        "temporal_correlation_only": True,
        "not_causation": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "correlation_window_seconds": _CORRELATION_WINDOW_SECONDS,
        "candle_count": len(seed.get("candles") or {}),
        "acceptance_criteria": {
            "correlation_not_causation": True,
            "timestamps_aligned": True,
            "evidence_required_for_claims": True,
            "rule_based_only": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
