"""
BLACKDARK — Wash trade guard (regulatory / user protection).

Blocks same-account offsetting buy+sell in a short window that could indicate
wash trading or attacker-driven fake volume after key compromise.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Literal

import config

logger = logging.getLogger("BLACKDARK.WashTradeGuard")

Side = Literal["buy", "sell"]

_recent: dict[str, list[tuple[float, Side]]] = {}
_blocked_total = 0


def _enabled() -> bool:
    return getattr(config, "WASH_TRADE_GUARD_ENABLED", True)


def _window_sec() -> float:
    return float(getattr(config, "WASH_TRADE_WINDOW_SEC", 300))


def _trade_key(user_id: int | None, exchange: str, symbol: str) -> str:
    uid = str(user_id or "operator")
    return f"{uid}|{exchange.lower()}|{symbol.upper()}"


def check_wash_trade(
    *,
    user_id: int | None,
    exchange: str,
    symbol: str,
    side: Side,
) -> tuple[bool, str]:
    """
    Return (allowed, reason). Blocks opposite-side trade within window on same account.
    """
    global _blocked_total

    if not _enabled():
        return True, "guard_disabled"

    key = _trade_key(user_id, exchange, symbol)
    now = time.monotonic()
    window = _window_sec()
    history = _recent.get(key, [])
    history = [(ts, s) for ts, s in history if now - ts <= window]

    opposite = "sell" if side == "buy" else "buy"
    if any(s == opposite for ts, s in history):
        _blocked_total += 1
        logger.warning(
            "Wash trade guard BLOCKED | user_id=%s exchange=%s symbol=%s side=%s",
            user_id,
            exchange,
            symbol,
            side,
        )
        return False, "wash_trade_opposite_side_window"

    history.append((now, side))
    _recent[key] = history
    return True, "ok"


def record_trade(
    *,
    user_id: int | None,
    exchange: str,
    symbol: str,
    side: Side,
) -> None:
    """Record executed trade (called after successful order)."""
    if not _enabled():
        return
    key = _trade_key(user_id, exchange, symbol)
    now = time.monotonic()
    history = _recent.get(key, [])
    history.append((now, side))
    _recent[key] = [(ts, s) for ts, s in history if now - ts <= _window_sec()]


def wash_trade_guard_status() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "window_sec": _window_sec(),
        "blocked_total": _blocked_total,
        "tracked_accounts": len(_recent),
        "policy": (
            "Blocks opposite-side orders on the same user/exchange/symbol within "
            "the configured window to reduce wash-trading and post-breach abuse."
        ),
    }
