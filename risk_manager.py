"""
BLACKDARK — Built-in Risk Management (Buyer Requirement #7).

- High slippage gate
- Data poisoning detection + trading freeze
- Automatic stop-loss on executed orders
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import config
from log_safety import sanitize_asset, sanitize_log_value

logger = logging.getLogger("BLACKDARK.RiskManager")

_freeze_until: float = 0.0
_freeze_reason: str = ""
_poison_events: list[dict[str, Any]] = []
_active_stop_losses: dict[str, dict[str, Any]] = {}
_bg_tasks: set[Any] = set()


@dataclass
class RiskVerdict:
    allowed: bool
    reason: str = ""
    slippage_bps: float = 0.0
    poison_detected: bool = False
    sentiment_blocked: bool = False


def _max_slippage_bps() -> float:
    return float(os.getenv("RISK_MAX_SLIPPAGE_BPS", "80"))


def _poison_threshold_pct() -> float:
    return float(os.getenv("RISK_POISON_PRICE_DEVIATION_PCT", "15.0"))


def _freeze_duration_sec() -> int:
    return int(os.getenv("RISK_POISON_FREEZE_SEC", "300"))


def _stop_loss_pct() -> float:
    return float(os.getenv("RISK_STOP_LOSS_PCT", "2.0"))


def is_trading_frozen() -> bool:
    global _freeze_until
    if time.time() < _freeze_until:
        return True
    if _freeze_until > 0:
        _freeze_until = 0.0
    return False


def freeze_trading(reason: str, *, duration_sec: int | None = None) -> dict[str, Any]:
    global _freeze_until, _freeze_reason
    dur = duration_sec if duration_sec is not None else _freeze_duration_sec()
    _freeze_until = time.time() + dur
    _freeze_reason = reason
    event = {"reason": reason, "duration_sec": dur, "ts": time.time()}
    _poison_events.append(event)
    if len(_poison_events) > 100:
        _poison_events.pop(0)
    logger.warning("TRADING FROZEN | reason=%s duration=%ss", sanitize_log_value(reason), dur)
    try:
        import asyncio

        from database import set_risk_freeze_state

        loop = asyncio.get_running_loop()
        task = loop.create_task(
            set_risk_freeze_state(
                frozen=True,
                reason=reason,
                until_ts=_freeze_until,
            )
        )
        _bg_tasks.add(task)
        task.add_done_callback(_bg_tasks.discard)
    except Exception:
        logger.debug("risk freeze persist skipped", exc_info=True)
    return {"frozen": True, "reason": reason, "until_ts": _freeze_until, "persistent": True}


def unfreeze_trading() -> dict[str, Any]:
    global _freeze_until, _freeze_reason
    _freeze_until = 0.0
    _freeze_reason = ""
    try:
        import asyncio

        from database import set_risk_freeze_state

        loop = asyncio.get_running_loop()
        task = loop.create_task(set_risk_freeze_state(frozen=False, reason="", until_ts=0.0))
        _bg_tasks.add(task)
        task.add_done_callback(_bg_tasks.discard)
    except Exception:
        logger.debug("risk unfreeze persist skipped", exc_info=True)
    return {"frozen": False, "persistent": True}


async def load_persistent_freeze() -> dict[str, Any]:
    """Restore freeze state from SQLite/Postgres after process restart."""
    global _freeze_until, _freeze_reason
    try:
        from database import fetch_risk_freeze_state

        row = await fetch_risk_freeze_state()
    except Exception:
        logger.debug("load_persistent_freeze unavailable", exc_info=True)
        return {"loaded": False}
    if not row or not row.get("frozen"):
        _freeze_until = 0.0
        _freeze_reason = ""
        return {"loaded": True, "frozen": False}
    until = float(row.get("until_ts") or 0)
    if until and until < time.time():
        _freeze_until = 0.0
        _freeze_reason = ""
        try:
            from database import set_risk_freeze_state

            await set_risk_freeze_state(frozen=False, reason="", until_ts=0.0)
        except Exception:
            pass
        return {"loaded": True, "frozen": False, "expired": True}
    _freeze_until = until if until > 0 else time.time() + _freeze_duration_sec()
    _freeze_reason = str(row.get("reason") or "persistent_freeze")
    logger.warning(
        "Restored persistent trading freeze | reason=%s",
        sanitize_log_value(_freeze_reason),
    )
    return {"loaded": True, "frozen": True, "reason": _freeze_reason, "until_ts": _freeze_until}


def detect_data_poisoning(
    prices: dict[str, float],
    *,
    reference_prices: dict[str, float] | None = None,
) -> RiskVerdict:
    """Flag prices deviating >threshold from median/reference (data poisoning)."""
    if not prices:
        return RiskVerdict(allowed=True)

    ref = reference_prices or {}
    threshold = _poison_threshold_pct()
    deviations: list[tuple[str, float]] = []

    if ref:
        for sym, px in prices.items():
            ref_px = ref.get(sym)
            if ref_px and ref_px > 0:
                dev = abs(px - ref_px) / ref_px * 100
                if dev > threshold:
                    deviations.append((sym, dev))
    else:
        vals = [v for v in prices.values() if v > 0]
        if len(vals) >= 2:
            median = sorted(vals)[len(vals) // 2]
            for sym, px in prices.items():
                if median > 0:
                    dev = abs(px - median) / median * 100
                    if dev > threshold:
                        deviations.append((sym, dev))

    if deviations:
        worst = max(deviations, key=lambda x: x[1])
        freeze_trading(
            f"data_poisoning:{worst[0]}:{worst[1]:.1f}pct_deviation"
        )
        return RiskVerdict(
            allowed=False,
            reason=f"data_poisoning ({worst[0]} {worst[1]:.1f}% deviation)",
            poison_detected=True,
        )
    return RiskVerdict(allowed=True)


def check_slippage(slippage_bps: float) -> RiskVerdict:
    max_bps = _max_slippage_bps()
    if slippage_bps > max_bps:
        return RiskVerdict(
            allowed=False,
            reason=f"slippage_too_high ({slippage_bps:.1f}bps > {max_bps}bps)",
            slippage_bps=slippage_bps,
        )
    return RiskVerdict(allowed=True, slippage_bps=slippage_bps)


def evaluate_execution_risk(
    opportunity: dict[str, Any],
    *,
    reference_prices: dict[str, float] | None = None,
) -> RiskVerdict:
    """Full pre-execution risk gate."""
    if is_trading_frozen():
        return RiskVerdict(allowed=False, reason=f"trading_frozen:{_freeze_reason}")

    slippage = float(opportunity.get("total_slippage_bps") or opportunity.get("slippage_bps") or 0)
    slip_verdict = check_slippage(slippage)
    if not slip_verdict.allowed:
        return slip_verdict

    asset = str(opportunity.get("asset") or "BTC")
    price = float(opportunity.get("buy_price") or opportunity.get("price") or 0)
    if price > 0:
        poison = detect_data_poisoning({asset: price}, reference_prices=reference_prices)
        if not poison.allowed:
            return poison

    from sentiment_gate import sentiment_allows_execution

    if not sentiment_allows_execution(asset):
        return RiskVerdict(
            allowed=False,
            reason="sentiment_extreme_fear",
            sentiment_blocked=True,
        )

    return RiskVerdict(allowed=True)


def register_stop_loss(
    symbol: str,
    entry_price: float,
    side: str,
    *,
    stop_pct: float | None = None,
) -> dict[str, Any]:
    pct = stop_pct if stop_pct is not None else _stop_loss_pct()
    stop_price = entry_price * (1 - pct / 100) if side == "buy" else entry_price * (1 + pct / 100)

    record = {
        "symbol": symbol.upper(),
        "entry_price": entry_price,
        "stop_price": round(stop_price, 8),
        "stop_pct": pct,
        "side": side,
        "created_ts": time.time(),
        "triggered": False,
    }
    _active_stop_losses[symbol.upper()] = record
    logger.info(
        "Stop-loss registered | %s entry=%.4f stop=%.4f",
        sanitize_asset(symbol),
        entry_price,
        stop_price,
    )
    return record


def check_stop_losses(current_prices: dict[str, float]) -> list[dict[str, Any]]:
    """Return triggered stop-loss orders; marks them triggered."""
    triggered: list[dict[str, Any]] = []
    for sym, sl in list(_active_stop_losses.items()):
        if sl.get("triggered"):
            continue
        px = current_prices.get(sym)
        if px is None:
            continue
        hit = False
        if (sl["side"] == "buy" and px <= sl["stop_price"]) or (sl["side"] == "sell" and px >= sl["stop_price"]):
            hit = True
        if hit:
            sl["triggered"] = True
            sl["trigger_price"] = px
            sl["triggered_ts"] = time.time()
            triggered.append(dict(sl))
            logger.warning(
                "STOP-LOSS TRIGGERED | %s price=%.4f stop=%.4f",
                sanitize_asset(sym),
                px,
                sl["stop_price"],
            )
    return triggered


def active_stop_loss_symbols() -> list[str]:
    """Symbols with an untriggered stop-loss (for monitor loops)."""
    return [sym for sym, sl in _active_stop_losses.items() if not sl.get("triggered")]


def risk_status() -> dict[str, Any]:
    reason = _freeze_reason if is_trading_frozen() else ""
    return {
        "trading_frozen": is_trading_frozen(),
        "freeze_reason": reason,
        "freeze_until_ts": _freeze_until if is_trading_frozen() else None,
        "drift_freeze_active": str(reason).startswith("ml_drift_high"),
        "max_slippage_bps": _max_slippage_bps(),
        "poison_threshold_pct": _poison_threshold_pct(),
        "stop_loss_pct": _stop_loss_pct(),
        "active_stop_losses": len([s for s in _active_stop_losses.values() if not s.get("triggered")]),
        "recent_poison_events": _poison_events[-5:],
        "config_slippage_buffer_bps": config.SLIPPAGE_BUFFER_BPS,
        "honest_scope": {
            "shipped": [
                "slippage gate",
                "poison / freeze kill-switch",
                "stop-loss hooks",
                "drawdown freeze (when enabled)",
            ],
            "not_shipped": [
                "institutional VaR 99% desk",
                "Expected Shortfall / CVaR engine",
                "formal position-limit ledger",
            ],
            "note": "Risk Intelligence here is execution safety — not a full buy-side risk platform.",
        },
    }
