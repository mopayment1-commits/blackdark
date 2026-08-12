"""Streaming freshness truth — stale data cannot silently appear as LIVE."""

from __future__ import annotations

import time
from typing import Any

from canonical_data_layer import FreshnessClass, classify_freshness, normalize_ts


def label_tick(
    *,
    exchange: str,
    symbol: str,
    bid: float,
    ask: float,
    provider_ts_ms: int | float | None,
    max_live_age_sec: float = 2.0,
    max_degraded_age_sec: float = 10.0,
) -> dict[str, Any]:
    """Attach explicit freshness_class to a stream tick."""
    now_ms = int(time.time() * 1000)
    provider_ts = None
    if provider_ts_ms is not None:
        provider_ts = normalize_ts(provider_ts_ms)
    freshness = classify_freshness(
        provider_ts=provider_ts,
        max_live_age_sec=max_live_age_sec,
        max_degraded_age_sec=max_degraded_age_sec,
    )
    age_ms = None
    if provider_ts_ms is not None:
        age_ms = max(0, now_ms - int(provider_ts_ms))
    return {
        "exchange": str(exchange).strip().lower(),
        "symbol": str(symbol).strip().upper(),
        "bid": float(bid),
        "ask": float(ask),
        "provider_ts_ms": int(provider_ts_ms) if provider_ts_ms is not None else None,
        "ingest_ts_ms": now_ms,
        "age_ms": age_ms,
        "freshness_class": freshness.value,
        "is_live": freshness is FreshnessClass.LIVE,
        # Never advertise LIVE unless freshness_class says so.
        "stream_status": freshness.value,
    }


def reject_stale_as_live(tick: dict[str, Any]) -> dict[str, Any]:
    """Fail closed if a consumer attempts to treat non-LIVE as LIVE."""
    out = dict(tick)
    fc = str(out.get("freshness_class") or out.get("stream_status") or "UNKNOWN")
    if out.get("is_live") and fc != FreshnessClass.LIVE.value:
        raise ValueError(f"stale_as_live_forbidden:{fc}")
    if fc != FreshnessClass.LIVE.value:
        out["is_live"] = False
        out["executable_quotes"] = False
    else:
        out["executable_quotes"] = True
    return out


def fanout_safe(tick: dict[str, Any]) -> dict[str, Any]:
    """Normalize fanout payload so Redis/UI cannot mislabel STALE as LIVE."""
    labeled = reject_stale_as_live(tick)
    if labeled.get("freshness_class") != FreshnessClass.LIVE.value:
        labeled["display_badge"] = labeled["freshness_class"]
        labeled.pop("LIVE", None)
    else:
        labeled["display_badge"] = "LIVE"
    return labeled
