"""
BLACKDARK — HFT tick sanitization (anti-spoofing).

Filters: price spikes, low-liquidity ghost orders, stale timestamp drift.
Non-custodial — read-only market data validation.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.PriceSanitize")

_mid_history: dict[str, list[tuple[int, float]]] = {}
_rejected: dict[str, int] = {"spike": 0, "ghost": 0, "stale": 0, "crossed": 0, "zscore": 0}
_data_anomalies: deque[dict[str, Any]] = deque(maxlen=500)


def _zscore_max() -> float:
    return float(getattr(config, "HFT_ZSCORE_MAX", 3.0))


def _zscore_min_dev_pct() -> float:
    return float(getattr(config, "HFT_ZSCORE_MIN_DEV_PCT", 0.05))


def _outlier_max_pct() -> float:
    return float(getattr(config, "HFT_OUTLIER_MAX_PCT", 5.0))


def _std_mids(mids: list[float]) -> float:
    if len(mids) < 2:
        return 0.0
    mean = sum(mids) / len(mids)
    var = sum((m - mean) ** 2 for m in mids) / len(mids)
    return var ** 0.5


def _log_data_anomaly(exchange: str, symbol: str, reason: str, mid: float, ref: float) -> None:
    row = {
        "exchange": exchange.lower(),
        "symbol": symbol.upper(),
        "reason": reason,
        "mid": round(mid, 8),
        "reference": round(ref, 8),
        "deviation_pct": round(abs(mid - ref) / ref * 100, 3) if ref > 0 else 0.0,
    }
    _data_anomalies.append(row)
    logger.warning("Data_Anomaly | %s %s | %s | mid=%s ref=%s", exchange, symbol, reason, mid, ref)


def data_anomaly_log(limit: int = 20) -> list[dict[str, Any]]:
    return list(_data_anomalies)[-limit:]


def _enabled() -> bool:
    return getattr(config, "HFT_SANITIZE_ENABLED", True)


def _key(exchange: str, symbol: str) -> str:
    return f"{exchange.lower()}|{symbol.upper()}"


def _min_notional_usd() -> float:
    return float(getattr(config, "HFT_MIN_ORDER_NOTIONAL_USD", 50.0))


def _max_spike_bps() -> float:
    return float(getattr(config, "HFT_OUTLIER_MAX_BPS", 500.0))


def _max_ts_drift_ms() -> float:
    return float(getattr(config, "HFT_MAX_TS_DRIFT_MS", 2000.0))


def _history_window_ms() -> int:
    return int(getattr(config, "HFT_SANITIZE_HISTORY_MS", 60_000))


@dataclass
class SanitizeResult:
    accepted: bool
    reason: str
    bid: float
    ask: float
    bid_qty: float
    ask_qty: float
    mid: float
    ts_ms: int


def _record_reject(kind: str) -> None:
    _rejected[kind] = _rejected.get(kind, 0) + 1


def _median_mid(key: str) -> float | None:
    hist = _mid_history.get(key) or []
    if len(hist) < 5:
        return None
    mids = sorted(m for _, m in hist)
    return mids[len(mids) // 2]


def _warmup_samples() -> int:
    return int(getattr(config, "HFT_SANITIZE_WARMUP_SAMPLES", 5))


def sanitize_tick(
    exchange: str,
    symbol: str,
    *,
    bid: float,
    ask: float,
    bid_qty: float,
    ask_qty: float,
    ts_ms: int | None = None,
) -> SanitizeResult:
    """Validate one WS tick before hot storage / arbitrage."""
    now_ms = int(time.time() * 1000)
    ts = ts_ms or now_ms
    mid = (bid + ask) / 2.0 if bid > 0 and ask > 0 else 0.0

    base = SanitizeResult(
        accepted=True,
        reason="ok",
        bid=bid,
        ask=ask,
        bid_qty=bid_qty,
        ask_qty=ask_qty,
        mid=mid,
        ts_ms=ts,
    )

    if not _enabled():
        return base

    sym = str(symbol or "").strip().upper()
    if not sym or "/" not in sym:
        _record_reject("crossed")
        return SanitizeResult(False, "invalid_symbol", bid, ask, bid_qty, ask_qty, mid, ts)

    if bid <= 0 or ask <= 0 or ask < bid:
        _record_reject("crossed")
        return SanitizeResult(False, "crossed_or_invalid_book", bid, ask, bid_qty, ask_qty, mid, ts)

    drift = abs(now_ms - ts)
    if drift > _max_ts_drift_ms():
        _record_reject("stale")
        return SanitizeResult(False, f"stale_ts_drift_{drift:.0f}ms", bid, ask, bid_qty, ask_qty, mid, ts)

    bid_notional = bid * max(bid_qty, 0.0)
    ask_notional = ask * max(ask_qty, 0.0)
    min_n = _min_notional_usd()
    if bid_notional < min_n and ask_notional < min_n:
        _record_reject("ghost")
        return SanitizeResult(False, "ghost_low_liquidity", bid, ask, bid_qty, ask_qty, mid, ts)

    key = _key(exchange, sym)
    hist = _mid_history.setdefault(key, [])
    hist.append((ts, mid))
    cutoff = now_ms - _history_window_ms()
    _mid_history[key] = [(t, m) for t, m in hist if t >= cutoff][-500:]

    mids = sorted(m for _, m in _mid_history[key])
    if len(mids) < _warmup_samples():
        return base

    ref = _median_mid(key)
    if ref and ref > 0:
        dev_pct = abs(mid - ref) / ref * 100
        spike_bps = dev_pct * 100
        std = _std_mids(mids)
        min_std = ref * 1e-5
        z_score = abs(mid - ref) / std if std > min_std else 0.0

        if dev_pct > _outlier_max_pct() or (
            std > min_std and z_score > _zscore_max() and dev_pct >= _zscore_min_dev_pct()
        ):
            _record_reject("zscore")
            reason = f"data_anomaly_z{z_score:.1f}_pct{dev_pct:.1f}"
            _log_data_anomaly(exchange, sym, reason, mid, ref)
            return SanitizeResult(False, reason, bid, ask, bid_qty, ask_qty, mid, ts)

        if spike_bps > _max_spike_bps():
            _record_reject("spike")
            return SanitizeResult(False, f"price_spike_{spike_bps:.0f}bps", bid, ask, bid_qty, ask_qty, mid, ts)

    return base


def sanitize_stats() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "rejected": dict(_rejected),
        "tracked_symbols": len(_mid_history),
        "min_notional_usd": _min_notional_usd(),
        "max_spike_bps": _max_spike_bps(),
        "max_ts_drift_ms": _max_ts_drift_ms(),
        "zscore_max": _zscore_max(),
        "outlier_max_pct": _outlier_max_pct(),
        "recent_anomalies": data_anomaly_log(5),
    }


def clear_sanitize_state() -> None:
    """Test helper — reset mid history between isolated test runs."""
    _mid_history.clear()
    _rejected.clear()
    _data_anomalies.clear()
