"""
OHLCV Core Feed — Feature #217 (Sprint 0).

Unified candle aggregation with interval exactness, multi-source aggregation
(min 3 sources), gap handling, and volume validation.
NOT sub-second — OHLCV is batch; real-time ticks are #212.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OHLCVCore")

_FEATURE_ID = 217
_SEED_PATH = Path("data/ohlcv_core_seed.json")
_STORE_PATH = Path("data/ohlcv_core_feed.json")
_MIN_SOURCES = 3

Interval = Literal["1m", "5m", "15m", "1h", "4h", "1d"]

_INTERVAL_MINUTES: dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> list[dict[str, Any]]:
    if not _SEED_PATH.is_file():
        return []
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("ohlcv core seed load failed: %s", exc)
        return []


def _load_store() -> dict[str, Any]:
    if _STORE_PATH.is_file():
        try:
            return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    store = {"candles": _load_seed(), "updated_at": _utcnow()}
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")
    return store


def validate_interval_exactness(open_time_utc: str, close_time_utc: str, interval: str) -> dict[str, Any]:
    """Interval exactness — 1H candle closes at :00, not arbitrary timestamps."""
    try:
        open_dt = datetime.fromisoformat(open_time_utc.replace("Z", "+00:00"))
        close_dt = datetime.fromisoformat(close_time_utc.replace("Z", "+00:00"))
    except ValueError:
        return {"exact": False, "reason": "invalid_timestamp"}

    minutes = _INTERVAL_MINUTES.get(interval, 60)
    duration = (close_dt - open_dt).total_seconds() / 60
    exact_duration = duration == minutes

    boundary_ok = True
    if interval == "1h":
        boundary_ok = close_dt.minute == 0 and close_dt.second == 0
    elif interval == "4h":
        boundary_ok = close_dt.hour % 4 == 0 and close_dt.minute == 0
    elif interval == "1d":
        boundary_ok = close_dt.hour == 0 and close_dt.minute == 0

    exact = exact_duration and boundary_ok
    display = (
        f"{interval.upper()} candle closes at exact boundary"
        if exact
        else f"Interval boundary violation: {interval} expected {minutes}min at :00"
    )
    return {
        "exact": exact,
        "interval": interval,
        "duration_minutes": duration,
        "expected_minutes": minutes,
        "boundary_ok": boundary_ok,
        "display": display,
    }


def _aggregate_sources(sources: dict[str, Any]) -> dict[str, Any]:
    """Multi-source aggregation — min 3 sources per asset."""
    available = {k: v for k, v in sources.items() if v.get("available", True)}
    down = [k for k, v in sources.items() if not v.get("available", True)]

    if len(available) < _MIN_SOURCES:
        gap_display = f"Missing data: {', '.join(down) or 'insufficient sources'} down | Interpolated: No"
    else:
        gap_display = f"Sources: {len(available)}/{len(sources)} live | Interpolated: No"

    if not available:
        return {
            "open": None, "high": None, "low": None, "close": None, "volume": None,
            "source_count": 0, "gap_display": gap_display, "interpolated": False,
        }

    vals = list(available.values())
    return {
        "open": vals[0]["open"],
        "high": max(v["high"] for v in vals),
        "low": min(v["low"] for v in vals),
        "close": vals[-1]["close"],
        "volume": round(sum(v["volume"] for v in vals), 2),
        "source_count": len(available),
        "sources_used": list(available.keys()),
        "gap_display": gap_display,
        "interpolated": False,
    }


def _validate_volume(aggregated_volume: float, onchain_proxy: float | None) -> dict[str, Any]:
    """Volume validation — cross-check exchange reported vs on-chain proxy."""
    if onchain_proxy is None or aggregated_volume is None:
        return {"validated": False, "reason": "insufficient_data"}
    ratio = aggregated_volume / onchain_proxy if onchain_proxy > 0 else 0
    validated = 0.1 <= ratio <= 10.0
    return {
        "validated": validated,
        "exchange_volume": aggregated_volume,
        "onchain_proxy": onchain_proxy,
        "ratio": round(ratio, 3),
        "display": f"Volume cross-check: {'PASS' if validated else 'REVIEW'} (ratio {ratio:.2f})",
    }


def _enrich_candle(row: dict[str, Any]) -> dict[str, Any]:
    interval = row.get("interval", "1h")
    exactness = validate_interval_exactness(
        row.get("open_time_utc", ""),
        row.get("close_time_utc", ""),
        interval,
    )
    agg = _aggregate_sources(row.get("sources") or {})
    vol_check = _validate_volume(agg.get("volume"), row.get("onchain_volume_proxy"))

    return {
        **row,
        "ohlcv": {
            "open": agg["open"],
            "high": agg["high"],
            "low": agg["low"],
            "close": agg["close"],
            "volume": agg["volume"],
        },
        "interval_exactness": exactness,
        "multi_source": {
            "min_sources": _MIN_SOURCES,
            "source_count": agg["source_count"],
            "sources_used": agg.get("sources_used", []),
            "gap_display": agg["gap_display"],
            "interpolated": agg["interpolated"],
        },
        "volume_validation": vol_check,
        "batch_not_realtime": True,
        "display": (
            f"{row.get('asset')} {interval.upper()} | "
            f"O:{agg['open']} H:{agg['high']} L:{agg['low']} C:{agg['close']} V:{agg['volume']}"
        ),
    }


def list_ohlcv_candles(
    *,
    asset: str | None = None,
    interval: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    store = _load_store()
    rows = [_enrich_candle(r) for r in store.get("candles") or []]

    if asset:
        rows = [r for r in rows if str(r.get("asset", "")).upper() == asset.upper()]
    if interval:
        rows = [r for r in rows if str(r.get("interval", "")).lower() == interval.lower()]

    rows.sort(key=lambda r: r.get("open_time_utc") or "", reverse=True)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "mode": "ohlcv_core_feed",
        "batch_not_realtime": True,
        "interval_exactness_required": True,
        "min_sources_per_asset": _MIN_SOURCES,
        "count": len(rows[:limit]),
        "candles": rows[:limit],
        "timestamp": _utcnow(),
    }


def get_ohlcv_candle(candle_id: str) -> dict[str, Any]:
    store = _load_store()
    for row in store.get("candles") or []:
        if row.get("id") == candle_id:
            return {
                "ok": True,
                "feature_id": _FEATURE_ID,
                "candle": _enrich_candle(row),
                "timestamp": _utcnow(),
            }
    return {"ok": False, "error": "candle_not_found"}


def ohlcv_core_feed_status() -> dict[str, Any]:
    store = _load_store()
    candles = store.get("candles") or []
    assets = {c.get("asset") for c in candles}
    intervals = {c.get("interval") for c in candles}
    exact_count = sum(
        1 for c in candles
        if validate_interval_exactness(
            c.get("open_time_utc", ""), c.get("close_time_utc", ""), c.get("interval", "1h")
        ).get("exact")
    )

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "module": "OHLCV Core Feed",
        "sprint": 0,
        "candle_count": len(candles),
        "asset_count": len(assets),
        "intervals": sorted(intervals),
        "interval_exactness": True,
        "exact_candle_count": exact_count,
        "min_sources_per_asset": _MIN_SOURCES,
        "gap_handling": True,
        "volume_validation": True,
        "batch_not_realtime": True,
        "realtime_ticks_feature": 212,
        "timestamp": _utcnow(),
    }
