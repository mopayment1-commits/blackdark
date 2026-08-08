"""Napoleon AM-style drawdown guard — extends risk_manager."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger("BLACKDARK.DrawdownGuard")

_peak_equity: float = 0.0
_current_equity: float = 0.0
_events: list[dict[str, Any]] = []


def _max_drawdown_pct() -> float:
    return float(os.getenv("RISK_MAX_DRAWDOWN_PCT", "8.0"))


def update_equity(equity_usd: float) -> dict[str, Any]:
    global _peak_equity, _current_equity
    _current_equity = max(0.0, float(equity_usd))
    _peak_equity = max(_peak_equity, _current_equity)
    drawdown_pct = 0.0
    if _peak_equity > 0:
        drawdown_pct = ((_peak_equity - _current_equity) / _peak_equity) * 100.0
    breached = drawdown_pct >= _max_drawdown_pct()
    payload = {
        "equity_usd": round(_current_equity, 2),
        "peak_equity_usd": round(_peak_equity, 2),
        "drawdown_pct": round(drawdown_pct, 3),
        "max_allowed_drawdown_pct": _max_drawdown_pct(),
        "breached": breached,
    }
    if breached:
        from risk_manager import freeze_trading

        freeze = freeze_trading(
            f"drawdown_guard:{drawdown_pct:.2f}%>={_max_drawdown_pct()}%",
            duration_sec=int(os.getenv("RISK_DRAWDOWN_FREEZE_SEC", "600")),
        )
        payload["freeze"] = freeze
        _events.append({"ts": time.time(), **payload})
    return payload


def drawdown_status() -> dict[str, Any]:
    dd = 0.0
    if _peak_equity > 0:
        dd = ((_peak_equity - _current_equity) / _peak_equity) * 100.0
    return {
        "equity_usd": _current_equity,
        "peak_equity_usd": _peak_equity,
        "drawdown_pct": round(dd, 3),
        "max_allowed_drawdown_pct": _max_drawdown_pct(),
        "recent_events": _events[-10:],
        "reference": "Napoleon AM drawdown discipline",
    }
