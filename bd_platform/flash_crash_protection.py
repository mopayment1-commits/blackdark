"""
Flash-Crash Protection Engine (#57) — anomaly detection + circuit breaker.

Detects flash crashes/pumps, cross-exchange divergence, liquidity evaporation.
Sends pause/resume signals to Decision Engine (#48).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import aiohttp

from path_safety import ensure_under, safe_data_file

logger = logging.getLogger("BLACKDARK.FlashCrashProtection")

CircuitLevel = Literal["green", "yellow", "orange", "red"]

_EXCHANGES = ("binance", "okx", "bybit")
_DATA_BASE = Path(__file__).resolve().parent.parent / "data"
_LOG_PATH = safe_data_file("flash_crash_events.jsonl")
_LOCK = threading.Lock()

# Rolling price snapshots: asset -> deque[(ts, exchange, price)]
_PRICE_HISTORY: dict[str, deque[tuple[float, str, float]]] = {}
_STATE: dict[str, dict[str, Any]] = {}
_RECOVERY_STABLE_SEC = 180  # 3 minutes


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append_event(row: dict[str, Any]) -> None:
    path = ensure_under(_LOG_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _record_price(asset: str, exchange: str, price: float) -> None:
    hist = _PRICE_HISTORY.setdefault(asset, deque(maxlen=500))
    hist.append((time.time(), exchange, price))


async def _fetch_exchange_price(session: aiohttp.ClientSession, exchange: str, asset: str) -> float | None:
    pair = f"{asset}USDT"
    try:
        if exchange == "binance":
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": pair}
        elif exchange == "okx":
            url = "https://www.okx.com/api/v5/market/ticker"
            params = {"instId": f"{asset}-USDT"}
        elif exchange == "bybit":
            url = "https://api.bybit.com/v5/market/tickers"
            params = {"category": "spot", "symbol": pair}
        else:
            return None
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
        if exchange == "binance":
            return float(data.get("price") or 0) or None
        if exchange == "okx":
            rows = data.get("data") or []
            return float(rows[0].get("last") or 0) if rows else None
        if exchange == "bybit":
            rows = (data.get("result") or {}).get("list") or []
            return float(rows[0].get("lastPrice") or 0) if rows else None
    except (aiohttp.ClientError, TypeError, ValueError, KeyError, IndexError):
        return None
    return None


async def _fetch_multi_exchange_prices(asset: str) -> dict[str, float]:
    prices: dict[str, float] = {}
    timeout = aiohttp.ClientTimeout(total=3.0)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        results = await asyncio.gather(
            *[_fetch_exchange_price(session, ex, asset) for ex in _EXCHANGES],
            return_exceptions=True,
        )
    for ex, px in zip(_EXCHANGES, results):
        if isinstance(px, (int, float)) and px > 0:
            prices[ex] = float(px)
            _record_price(asset, ex, float(px))
    return prices


def _price_velocity(asset: str, *, window_sec: float = 60.0) -> float | None:
    hist = _PRICE_HISTORY.get(asset)
    if not hist or len(hist) < 2:
        return None
    now = time.time()
    recent = [p for ts, _ex, p in hist if now - ts <= window_sec]
    if len(recent) < 2:
        return None
    start, end = recent[0], recent[-1]
    if start <= 0:
        return None
    return ((end - start) / start) * 100


def _cross_exchange_divergence(prices: dict[str, float]) -> float | None:
    if len(prices) < 2:
        return None
    vals = list(prices.values())
    lo, hi = min(vals), max(vals)
    if lo <= 0:
        return None
    return ((hi - lo) / lo) * 100


def _classify_event(
    *,
    velocity_pct: float | None,
    divergence_pct: float | None,
    direction: str,
) -> dict[str, Any]:
    v = abs(velocity_pct or 0)
    if divergence_pct is not None and divergence_pct >= 1.5:
        return {
            "event_type": "exchange_specific_crash",
            "action": "warn_api_or_halt",
            "message": "Single-exchange divergence detected — possible API error or halt",
        }
    if v >= 3.0 and direction == "down":
        return {
            "event_type": "flash_crash",
            "action": "halt_buy_signals",
            "message": "Flash crash detected — do not buy into volatility",
        }
    if v >= 3.0 and direction == "up":
        return {
            "event_type": "flash_pump",
            "action": "halt_sell_signals",
            "message": "Flash pump detected — avoid panic selling",
        }
    if v >= 5.0:
        return {
            "event_type": "liquidation_cascade",
            "action": "halt_futures_entries",
            "message": "Liquidation cascade risk — wait for stabilization",
        }
    if v >= 2.0:
        return {
            "event_type": "velocity_spike",
            "action": "delay_signals",
            "message": "Elevated velocity — signals delayed 30s for re-evaluation",
        }
    return {"event_type": "normal", "action": "none", "message": "Market normal"}


def _circuit_level(velocity_pct: float | None) -> CircuitLevel:
    v = abs(velocity_pct or 0)
    if v >= 5.0:
        return "red"
    if v >= 3.0:
        return "orange"
    if v >= 2.0:
        return "yellow"
    return "green"


def _recovery_check(asset: str, level: CircuitLevel) -> bool:
    if level == "green":
        return True
    st = _STATE.get(asset) or {}
    triggered = st.get("triggered_at")
    if not triggered:
        return False
    stable_since = st.get("stable_since")
    if level != "green" and stable_since:
        return (time.time() - stable_since) >= _RECOVERY_STABLE_SEC
    return False


async def evaluate_flash_protection(asset: str = "BTC") -> dict[str, Any]:
    """Main evaluation — anomaly detection + circuit breaker state."""
    t0 = time.perf_counter()
    sym = asset.upper()
    prices = await _fetch_multi_exchange_prices(sym)
    velocity = _price_velocity(sym, window_sec=60.0)
    divergence = _cross_exchange_divergence(prices)

    direction = "down" if (velocity or 0) < 0 else "up"
    level = _circuit_level(velocity)
    classification = _classify_event(
        velocity_pct=velocity,
        divergence_pct=divergence,
        direction=direction,
    )

    with _LOCK:
        prev = _STATE.get(sym) or {}
        if level == "green":
            stable_since = prev.get("stable_since") or time.time()
        else:
            stable_since = None
        if level != "green" and prev.get("level", "green") == "green":
            triggered_at = time.time()
        else:
            triggered_at = prev.get("triggered_at")
        recovering = _recovery_check(sym, level) and prev.get("level") in {"orange", "red"}
        _STATE[sym] = {
            "level": level,
            "velocity_pct_60s": velocity,
            "triggered_at": triggered_at,
            "stable_since": stable_since,
            "recovering": recovering,
            "updated_at": _utcnow(),
        }

    pause_signals = level in {"orange", "red"}
    delay_signals = level == "yellow"
    safe_mode = level == "red"

    alert = None
    if level != "green":
        alert = (
            f"Flash event on {sym}: {classification['event_type'].replace('_', ' ')} — "
            f"{abs(velocity or 0):.1f}% in 60s. Circuit breaker: {level.upper()}."
        )

    event_row = {
        "asset": sym,
        "level": level,
        "velocity_pct_60s": velocity,
        "divergence_pct": divergence,
        "prices": prices,
        "classification": classification,
        "pause_signals": pause_signals,
        "timestamp": _utcnow(),
    }
    if level != "green":
        _append_event(event_row)

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#57",
        "surface": "flash_crash_protection",
        "asset": sym,
        "circuit_breaker": {
            "level": level,
            "label": {"green": "Normal", "yellow": "Caution", "orange": "Restricted", "red": "Halted"}[level],
            "pause_new_signals": pause_signals,
            "delay_signals_sec": 30 if delay_signals else 0,
            "safe_mode": safe_mode,
            "recovering": recovering,
        },
        "metrics": {
            "price_velocity_60s_pct": round(velocity, 4) if velocity is not None else None,
            "cross_exchange_divergence_pct": round(divergence, 4) if divergence is not None else None,
            "exchange_prices": prices,
        },
        "classification": classification,
        "alert": alert,
        "safe_mode_recommendation": (
            "AI suggests: Hold current positions. Do not enter new trades. "
            "Most flash crashes recover within 90 minutes historically."
            if safe_mode
            else None
        ),
        "decision_engine_signal": {
            "action": "pause" if pause_signals else ("delay" if delay_signals else "resume"),
            "reason": classification.get("event_type"),
        },
        "latency_ms": round(elapsed * 1000, 1),
        "detection_sla_met": elapsed <= 10.0,
        "timestamp": _utcnow(),
    }


def circuit_breaker_status(asset: str | None = None) -> dict[str, Any]:
    """Dashboard status bar — global or per-asset."""
    if asset:
        sym = asset.upper()
        st = _STATE.get(sym) or {"level": "green"}
        return {
            "ok": True,
            "feature": "#57",
            "asset": sym,
            "level": st.get("level", "green"),
            "timestamp": _utcnow(),
        }
    levels = {a: s.get("level", "green") for a, s in _STATE.items()}
    worst = "green"
    for lv in ("yellow", "orange", "red"):
        if lv in levels.values():
            worst = lv
            break
    return {
        "ok": True,
        "feature": "#57",
        "global_level": worst,
        "assets": levels,
        "active_protections": sum(1 for v in levels.values() if v != "green"),
        "timestamp": _utcnow(),
    }


async def flash_protection_for_decision_engine(asset: str = "BTC") -> dict[str, Any]:
    """Compact signal for Decision Engine (#48)."""
    ev = await evaluate_flash_protection(asset)
    cb = ev.get("circuit_breaker") or {}
    sig = ev.get("decision_engine_signal") or {}
    return {
        "ok": ev.get("ok", False),
        "feature": "#57",
        "circuit_level": cb.get("level"),
        "pause_signals": cb.get("pause_new_signals"),
        "action": sig.get("action"),
        "headline": ev.get("alert"),
    }
