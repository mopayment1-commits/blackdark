"""
Strategy Lab Replay Mode (#92) — AI-powered historical replay with zero future leakage.

NOT basic TradingView bar replay — users see what AI would have signaled at each bar
vs actual outcome. All features computed strictly from data[:bar_index+1].

Acceptance: No future data leakage (purged, point-in-time only).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import aiohttp

logger = logging.getLogger("BLACKDARK.StrategyLabReplay")

_SESSIONS_PATH = Path("data/strategy_lab_sessions.json")
_MIN_BARS = 48
_DEFAULT_ASSETS = ("BTC", "ETH", "SOL", "BNB", "XRP")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class PurgedBarSeries:
    """OHLCV bars with strict as-of indexing — no future access."""

    asset: str
    interval: str
    bars: list[dict[str, Any]]
    source: str

    def __len__(self) -> int:
        return len(self.bars)

    def view_as_of(self, bar_index: int) -> list[dict[str, Any]]:
        """Return bars[0:bar_index+1] only — raises if future peek attempted."""
        if bar_index < 0 or bar_index >= len(self.bars):
            raise IndexError(f"bar_index {bar_index} out of range [0, {len(self.bars)})")
        return self.bars[: bar_index + 1]

    def bar(self, bar_index: int) -> dict[str, Any]:
        return self.bars[bar_index]

    def closes_as_of(self, bar_index: int) -> list[float]:
        return [float(b["close"]) for b in self.view_as_of(bar_index)]


def _returns(closes: list[float]) -> dict[str, float]:
    if len(closes) < 2:
        return {"ret_1": 0.0, "ret_4": 0.0, "ret_24": 0.0, "volatility": 0.0}
    last = closes[-1]
    ret_1 = (last / closes[-2] - 1.0) * 100
    ret_4 = (last / closes[-5] - 1.0) * 100 if len(closes) >= 5 else ret_1
    ret_24 = (last / closes[-25] - 1.0) * 100 if len(closes) >= 25 else ret_4
    changes = [(closes[i] / closes[i - 1] - 1.0) * 100 for i in range(1, len(closes))]
    vol = sum(abs(c) for c in changes[-24:]) / max(len(changes[-24:]), 1)
    return {"ret_1": ret_1, "ret_4": ret_4, "ret_24": ret_24, "volatility": vol}


def point_in_time_decision_signal(
    closes: list[float],
    *,
    asset: str = "BTC",
) -> dict[str, Any]:
    """
    Point-in-time #48-style signal proxy — uses ONLY closes available at bar close.
    No live API calls; no future bars.
    """
    rets = _returns(closes)
    mom = rets["ret_24"]
    vol = max(rets["volatility"], 0.1)
    z = mom / vol

    if z > 1.2 and rets["ret_4"] > 0:
        action: Literal["buy", "sell", "hold"] = "buy"
        confidence = min(95.0, 55 + abs(z) * 12)
        reasoning = f"Momentum positive ({mom:.1f}% / 24 bars) with trend confirmation"
    elif z < -1.2 and rets["ret_4"] < 0:
        action = "sell"
        confidence = min(95.0, 55 + abs(z) * 12)
        reasoning = f"Momentum negative ({mom:.1f}% / 24 bars) with trend confirmation"
    else:
        action = "hold"
        confidence = max(40.0, 60 - abs(z) * 8)
        reasoning = f"Mixed signals — volatility {vol:.1f}%, 24-bar return {mom:.1f}%"

    return {
        "action": action,
        "confidence_pct": round(confidence, 1),
        "reasoning": reasoning,
        "feature_snapshot": rets,
        "asset": asset.upper(),
        "signal_source": "point_in_time_replay_v1",
        "future_data_used": False,
    }


def _outcome_after_bars(
    entry_close: float,
    future_closes: list[float],
    *,
    horizon: int = 24,
) -> dict[str, Any]:
    """Compute actual outcome from future bars (only revealed AFTER replay step)."""
    if not future_closes:
        return {"available": False}
    exit_px = future_closes[min(horizon, len(future_closes)) - 1]
    pnl_pct = ((exit_px / entry_close) - 1.0) * 100 if entry_close > 0 else 0.0
    direction = "up" if pnl_pct > 0 else "down" if pnl_pct < 0 else "flat"
    return {
        "available": True,
        "horizon_bars": horizon,
        "exit_price": round(exit_px, 6),
        "pnl_pct": round(pnl_pct, 3),
        "direction": direction,
    }


async def fetch_ohlcv_series(
    asset: str,
    *,
    interval: str = "1h",
    limit: int = 500,
) -> PurgedBarSeries:
    """Load historical OHLCV — archive first, then public kline mirrors."""
    sym = asset.upper()
    bars: list[dict[str, Any]] = []
    source = "binance_klines_mirror"

    bars = await _fetch_klines(sym, interval=interval, limit=limit)

    if len(bars) < _MIN_BARS:
        raise ValueError(f"insufficient_ohlcv for {sym}: {len(bars)} bars")

    return PurgedBarSeries(asset=sym, interval=interval, bars=bars[-limit:], source=source)


async def _fetch_klines(asset: str, *, interval: str, limit: int) -> list[dict[str, Any]]:
    hosts = (
        "https://data-api.binance.vision",
        "https://api.binance.us",
        "https://api.binance.com",
    )
    params = {"symbol": f"{asset}USDT", "interval": interval, "limit": min(1000, limit)}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for host in hosts:
            try:
                async with session.get(f"{host}/api/v3/klines", params=params) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    if not isinstance(data, list):
                        continue
                    return [
                        {
                            "ts": int(k[0]),
                            "open": float(k[1]),
                            "high": float(k[2]),
                            "low": float(k[3]),
                            "close": float(k[4]),
                            "volume": float(k[5]),
                        }
                        for k in data
                        if isinstance(k, list) and len(k) >= 6
                    ]
            except (aiohttp.ClientError, TypeError, ValueError):
                continue
    return []


@dataclass
class ReplaySession:
    """Time-controlled playback session with leakage guards."""

    session_id: str
    series: PurgedBarSeries
    cursor: int = 0
    horizon_bars: int = 24
    steps: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)

    def current_bar(self) -> dict[str, Any]:
        return self.series.bar(self.cursor)

    def step(self) -> dict[str, Any]:
        """Advance one bar: AI prediction at close, outcome revealed from past horizon only."""
        idx = self.cursor
        if idx >= len(self.series) - self.horizon_bars - 1:
            return {"ok": False, "error": "replay_complete", "cursor": idx}

        closes = self.series.closes_as_of(idx)
        signal = point_in_time_decision_signal(closes, asset=self.series.asset)
        bar = self.series.bar(idx)

        # Outcome uses bars AFTER signal bar — only for comparison, not for signal
        future = [float(b["close"]) for b in self.series.bars[idx + 1 : idx + 1 + self.horizon_bars]]
        outcome = _outcome_after_bars(float(bar["close"]), future, horizon=self.horizon_bars)

        correct = None
        if outcome.get("available") and signal["action"] != "hold":
            if signal["action"] == "buy":
                correct = outcome["pnl_pct"] > 0
            elif signal["action"] == "sell":
                correct = outcome["pnl_pct"] < 0

        step_row = {
            "bar_index": idx,
            "timestamp": datetime.fromtimestamp(bar["ts"] / 1000, UTC).isoformat(),
            "close": bar["close"],
            "ai_signal": signal,
            "actual_outcome": outcome,
            "prediction_correct": correct,
            "no_future_leakage": True,
        }
        self.steps.append(step_row)
        self.cursor = idx + 1
        return {"ok": True, "step": step_row, "cursor": self.cursor, "remaining": len(self.series) - self.cursor - self.horizon_bars}

    def summary(self) -> dict[str, Any]:
        actionable = [s for s in self.steps if s["ai_signal"]["action"] != "hold"]
        correct = [s for s in actionable if s.get("prediction_correct")]
        return {
            "session_id": self.session_id,
            "asset": self.series.asset,
            "interval": self.series.interval,
            "steps_played": len(self.steps),
            "actionable_signals": len(actionable),
            "accuracy_pct": round(len(correct) / len(actionable) * 100, 1) if actionable else None,
            "no_future_leakage": True,
            "source": self.series.source,
        }


def _load_sessions() -> dict[str, Any]:
    if not _SESSIONS_PATH.exists():
        return {"sessions": {}}
    try:
        return json.loads(_SESSIONS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}}


def _save_session(session: ReplaySession) -> None:
    data = _load_sessions()
    data["sessions"][session.session_id] = {
        "session_id": session.session_id,
        "asset": session.series.asset,
        "interval": session.series.interval,
        "cursor": session.cursor,
        "horizon_bars": session.horizon_bars,
        "steps_count": len(session.steps),
        "summary": session.summary(),
        "created_at": session.created_at,
        "updated_at": _utcnow(),
    }
    _SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SESSIONS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


async def create_replay_session(
    asset: str = "BTC",
    *,
    interval: str = "1h",
    limit: int = 500,
    horizon_bars: int = 24,
) -> dict[str, Any]:
    """Start Strategy Lab replay session (#92)."""
    series = await fetch_ohlcv_series(asset, interval=interval, limit=limit)
    session_id = f"replay-{series.asset.lower()}-{int(datetime.now(UTC).timestamp())}"
    session = ReplaySession(session_id=session_id, series=series, horizon_bars=horizon_bars)
    _save_session(session)
    return {
        "ok": True,
        "feature": "#92",
        "surface": "strategy_lab_replay",
        "session_id": session_id,
        "asset": series.asset,
        "interval": interval,
        "total_bars": len(series),
        "playable_bars": len(series) - horizon_bars - 1,
        "data_source": series.source,
        "no_future_leakage": True,
        "first_bar": session.current_bar(),
        "timestamp": _utcnow(),
        "_session": session,  # in-memory for same-request stepping; API re-fetches for stateless
    }


async def run_replay_batch(
    asset: str = "BTC",
    *,
    interval: str = "1h",
    limit: int = 200,
    max_steps: int = 50,
    horizon_bars: int = 24,
) -> dict[str, Any]:
    """Run full replay batch — for API and tests."""
    series = await fetch_ohlcv_series(asset, interval=interval, limit=limit)
    session = ReplaySession(
        session_id=f"batch-{series.asset.lower()}",
        series=series,
        horizon_bars=horizon_bars,
    )
    played = 0
    while played < max_steps:
        result = session.step()
        if not result.get("ok"):
            break
        played += 1

    summary = session.summary()
    return {
        "ok": True,
        "feature": "#92",
        "surface": "strategy_lab_replay",
        "asset": series.asset,
        "steps": session.steps[-20:],
        "summary": summary,
        "no_future_leakage": True,
        "timestamp": _utcnow(),
    }


def replay_mode_status() -> dict[str, Any]:
    data = _load_sessions()
    return {
        "ok": True,
        "feature": "#92",
        "role": "strategy_lab_experience",
        "active_sessions": len(data.get("sessions") or {}),
        "no_future_leakage": True,
        "default_assets": list(_DEFAULT_ASSETS),
        "timestamp": _utcnow(),
    }
