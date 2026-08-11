"""
BLACKDARK — Flywheel saturation guard (crowd liquidity depletion mitigation).

When many subscribers act on the same arbitrage alert, competing orders deplete
book depth and inflate slippage — killing the edge for everyone. This guard:
  • Pre-simulates crowd notional before broadcasting alerts
  • Caps alert recipients and execution slots per opportunity
  • Re-walks order books after simulated prior takers
"""

from __future__ import annotations

import hashlib
import logging
import time
from copy import deepcopy
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.FlywheelSaturation")

_crowd_state: dict[str, dict[str, Any]] = {}
_blocked_alerts = 0
_blocked_executions = 0


def _enabled() -> bool:
    return getattr(config, "FLYWHEEL_SATURATION_GUARD_ENABLED", True)


def _ttl_sec() -> float:
    return float(getattr(config, "FLYWHEEL_CROWD_STATE_TTL_SEC", 120))


def _max_alert_recipients() -> int:
    return int(getattr(config, "FLYWHEEL_MAX_ALERT_RECIPIENTS", 50))


def _max_execution_slots() -> int:
    return int(getattr(config, "FLYWHEEL_MAX_EXECUTION_SLOTS_PER_OPP", 5))


def _per_actor_notional() -> float:
    return float(getattr(config, "FLYWHEEL_DEFAULT_COMPETING_NOTIONAL_USD", 100))


def _min_profit_after_crowd_usd() -> float:
    return float(getattr(config, "FLYWHEEL_MIN_PROFIT_AFTER_CROWD_USD", 0.05))


def opportunity_fingerprint(opportunity: dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(opportunity.get("kind") or ""),
            str(opportunity.get("asset") or opportunity.get("symbol") or ""),
            str(opportunity.get("buy_exchange") or opportunity.get("buy_venue") or ""),
            str(opportunity.get("sell_exchange") or opportunity.get("sell_venue") or ""),
        ]
    )
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _prune_state() -> None:
    cutoff = time.monotonic() - _ttl_sec()
    stale = [fp for fp, row in _crowd_state.items() if float(row.get("at") or 0) < cutoff]
    for fp in stale:
        _crowd_state.pop(fp, None)


def _state(fp: str) -> dict[str, Any]:
    _prune_state()
    row = _crowd_state.setdefault(fp, {"at": time.monotonic()})
    row["at"] = time.monotonic()
    return row


def deplete_asks_levels(levels: list[list[float]], quote_to_consume: float) -> list[list[float]]:
    if quote_to_consume <= 0 or not levels:
        return [list(level) for level in levels]
    remaining = quote_to_consume
    depleted: list[list[float]] = []
    for level in levels:
        price = float(level[0])
        amount = float(level[1])
        level_quote = price * amount
        if remaining >= level_quote:
            remaining -= level_quote
            continue
        if remaining > 0:
            partial_base = remaining / price
            depleted.append([price, max(0.0, amount - partial_base)])
            remaining = 0.0
        else:
            depleted.append([price, amount])
    return depleted


def deplete_bids_levels(levels: list[list[float]], base_to_consume: float) -> list[list[float]]:
    if base_to_consume <= 0 or not levels:
        return [list(level) for level in levels]
    remaining = base_to_consume
    depleted: list[list[float]] = []
    for level in levels:
        price = float(level[0])
        amount = float(level[1])
        if remaining >= amount:
            remaining -= amount
            continue
        if remaining > 0:
            depleted.append([price, max(0.0, amount - remaining)])
            remaining = 0.0
        else:
            depleted.append([price, amount])
    return depleted


async def estimate_pending_recipients() -> int:
    """Conservative estimate of users who may act on the next alert."""
    count = 0
    try:
        from database import fetch_active_alert_subscriptions, fetch_enabled_telegram_free_subscribers

        count += len(await fetch_active_alert_subscriptions())
        count += len(await fetch_enabled_telegram_free_subscribers())
    except Exception:
        logger.debug("Recipient estimate failed", exc_info=True)
    fallback = int(getattr(config, "FLYWHEEL_ESTIMATED_ACTORS_PER_ALERT", 10))
    return min(max(count, fallback), _max_alert_recipients())


def estimated_competing_notional(fingerprint: str, *, pending_recipients: int | None = None) -> float:
    row = _state(fingerprint)
    reserved = float(row.get("reserved_notional_usd") or 0)
    dispatched = int(row.get("alert_recipients") or 0)
    actors = dispatched if dispatched > 0 else (pending_recipients or 0)
    return reserved + actors * _per_actor_notional()


async def _fallback_rewalk(opportunity: dict[str, Any], notional: float | None) -> dict[str, Any]:
    from slippage_guard import rewalk_opportunity_slippage

    return await rewalk_opportunity_slippage(opportunity, quote_amount=notional)


def _crowd_depleted(opportunity: dict[str, Any], crowd_notional_usd: float, rewalk: str) -> dict[str, Any]:
    return {
        **opportunity,
        "executable": False,
        "cancel_reason": "crowd_liquidity_depleted",
        "flywheel_saturation": True,
        "flywheel_crowd_notional_usd": round(crowd_notional_usd, 2),
        "rewalk": rewalk,
    }


def _is_cross_exchange_kind(kind: str) -> bool:
    return kind in {"cross_exchange", "fast_cross", "stream_cross_exchange"}


def _crowd_books(
    books: dict[str, Any],
    *,
    buy_exchange: str,
    sell_exchange: str,
    symbol: str,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    buy_book_raw = (books.get(buy_exchange) or {}).get(symbol)
    sell_book_raw = (books.get(sell_exchange) or {}).get(symbol)
    if not buy_book_raw or not sell_book_raw:
        return None
    return deepcopy(buy_book_raw), deepcopy(sell_book_raw)


def _crowd_rewalk_success(
    opportunity: dict[str, Any],
    *,
    age_ms: float,
    crowd_notional_usd: float,
    total_slip: float,
    user_buy: Any,
    user_sell: Any,
    net_profit: float,
    verdict: Any,
) -> dict[str, Any]:
    updated = {
        **opportunity,
        "total_slippage_bps": round(total_slip, 2),
        "buy_slippage_bps": round(user_buy.slippage_bps, 2),
        "sell_slippage_bps": round(user_sell.slippage_bps, 2),
        "net_profit_usdt": round(net_profit, 4),
        "rewalk_age_ms": round(age_ms, 1),
        "executable": verdict.allowed and net_profit >= _min_profit_after_crowd_usd(),
        "rewalk": "crowd_adjusted_ok",
        "flywheel_saturation": True,
        "flywheel_crowd_notional_usd": round(crowd_notional_usd, 2),
        "flywheel_net_after_crowd_usd": round(net_profit, 4),
    }
    if not updated["executable"]:
        updated["cancel_reason"] = verdict.reason or "unprofitable_after_crowd"
    return updated


async def crowd_adjusted_rewalk(
    opportunity: dict[str, Any],
    *,
    crowd_notional_usd: float,
    user_notional_usd: float | None = None,
) -> dict[str, Any]:
    """Re-walk slippage after simulating prior crowd takers depleting depth."""
    if not _enabled() or crowd_notional_usd <= 0:
        return await _fallback_rewalk(opportunity, user_notional_usd)

    from live_book_hub import get_live_books_if_fresh

    fresh = get_live_books_if_fresh()
    if not fresh:
        return await _fallback_rewalk(opportunity, user_notional_usd)

    books, age_ms = fresh
    kind = str(opportunity.get("kind") or "")
    notional = user_notional_usd or float(opportunity.get("quote_amount") or config.DEFAULT_QUOTE_AMOUNT)
    buy_ex = str(opportunity.get("buy_exchange") or opportunity.get("buy_venue") or "").lower()
    sell_ex = str(opportunity.get("sell_exchange") or opportunity.get("sell_venue") or "").lower()
    asset = str(opportunity.get("asset") or "BTC")
    symbol = f"{asset}/USDT"

    if not _is_cross_exchange_kind(kind):
        updated = await _fallback_rewalk(opportunity, notional)
        updated["flywheel_crowd_notional_usd"] = round(crowd_notional_usd, 2)
        return updated

    try:
        from arbitrage_engine import walk_asks, walk_bids
    except ImportError:
        return await _fallback_rewalk(opportunity, notional)

    crowd_books = _crowd_books(books, buy_exchange=buy_ex, sell_exchange=sell_ex, symbol=symbol)
    if crowd_books is None:
        return await _fallback_rewalk(opportunity, notional)

    buy_book, sell_book = crowd_books
    buy_book["asks"] = deplete_asks_levels(buy_book.get("asks") or [], crowd_notional_usd)

    crowd_buy = walk_asks(buy_book, crowd_notional_usd)
    if crowd_buy is None:
        return _crowd_depleted(opportunity, crowd_notional_usd, "crowd_depleted_buy")

    sell_book["bids"] = deplete_bids_levels(sell_book.get("bids") or [], crowd_buy.base_amount)
    buy_book["asks"] = deplete_asks_levels(buy_book.get("asks") or [], crowd_notional_usd + notional)

    user_buy = walk_asks(buy_book, notional)
    if user_buy is None:
        return _crowd_depleted(opportunity, crowd_notional_usd, "crowd_depleted_user_buy")

    user_sell = walk_bids(sell_book, user_buy.base_amount)
    if user_sell is None:
        return _crowd_depleted(opportunity, crowd_notional_usd, "crowd_depleted_user_sell")

    total_slip = user_buy.slippage_bps + user_sell.slippage_bps
    from risk_manager import check_slippage

    verdict = check_slippage(total_slip)
    gross = user_sell.quote_value - user_buy.quote_cost
    from fee_matrix import trading_fees_usdt

    fees = trading_fees_usdt(buy_ex, notional) + trading_fees_usdt(sell_ex, user_sell.quote_value)
    net_profit = gross - fees

    return _crowd_rewalk_success(
        opportunity,
        age_ms=age_ms,
        crowd_notional_usd=crowd_notional_usd,
        total_slip=total_slip,
        user_buy=user_buy,
        user_sell=user_sell,
        net_profit=net_profit,
        verdict=verdict,
    )


async def apply_crowd_guard_to_alert(opportunity: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Returns (should_send, updated_opp) after crowd slippage simulation."""
    global _blocked_alerts
    if not _enabled():
        return True, opportunity

    fp = opportunity_fingerprint(opportunity)
    pending = await estimate_pending_recipients()
    crowd_notional = estimated_competing_notional(fp, pending_recipients=pending)
    updated = await crowd_adjusted_rewalk(opportunity, crowd_notional_usd=crowd_notional)

    if not updated.get("executable", True):
        _blocked_alerts += 1
        logger.info(
            "Alert blocked (flywheel saturation) | fp=%s crowd=$%.0f reason=%s",
            fp,
            crowd_notional,
            updated.get("cancel_reason"),
        )
        return False, updated

    updated["flywheel_alert_meta"] = {
        "estimated_recipients": pending,
        "estimated_crowd_notional_usd": round(crowd_notional, 2),
        "max_alert_recipients": _max_alert_recipients(),
    }
    return True, updated


def cap_alert_recipients(
    subscribers: list[dict[str, Any]],
    opportunity: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Limit mass alert fan-out to prevent self-inflicted liquidity depletion."""
    if not _enabled():
        return subscribers, {"capped": False}

    max_recipients = _max_alert_recipients()
    total = len(subscribers)
    if total <= max_recipients:
        return subscribers, {"capped": False, "total": total, "delivered": total}

    # Stable ordering: lower subscription id first (early subscribers priority)
    ordered = sorted(subscribers, key=lambda row: int(row.get("id") or 0))
    capped = ordered[:max_recipients]
    meta = {
        "capped": True,
        "total": total,
        "delivered": len(capped),
        "dropped": total - len(capped),
        "max_alert_recipients": max_recipients,
        "fingerprint": opportunity_fingerprint(opportunity) if opportunity else None,
    }
    logger.info(
        "Alert recipients capped | delivered=%s dropped=%s fp=%s",
        meta["delivered"],
        meta["dropped"],
        meta["fingerprint"],
    )
    return capped, meta


def register_alert_dispatch(opportunity: dict[str, Any], recipient_count: int) -> None:
    if not _enabled() or recipient_count <= 0:
        return
    fp = opportunity_fingerprint(opportunity)
    row = _state(fp)
    row["alert_recipients"] = int(row.get("alert_recipients") or 0) + recipient_count


def reserve_execution_slot(
    fingerprint: str,
    user_id: int | None,
    amount_usd: float,
) -> tuple[bool, str]:
    """Limit concurrent executors per opportunity fingerprint."""
    global _blocked_executions
    if not _enabled():
        return True, "ok"

    row = _state(fingerprint)
    slots: dict[str, float] = row.setdefault("execution_slots", {})
    uid = str(user_id or "anonymous")

    if uid in slots:
        return True, "already_reserved"

    if len(slots) >= _max_execution_slots():
        _blocked_executions += 1
        logger.info(
            "Execution slot denied (saturation) | fp=%s user=%s slots=%s",
            fingerprint,
            uid,
            len(slots),
        )
        return False, "execution_slots_saturated"

    slots[uid] = float(amount_usd)
    row["reserved_notional_usd"] = float(row.get("reserved_notional_usd") or 0) + float(amount_usd)
    return True, "ok"


def release_execution_slot(fingerprint: str, user_id: int | None, amount_usd: float) -> None:
    if not _enabled():
        return
    row = _crowd_state.get(fingerprint)
    if not row:
        return
    uid = str(user_id or "anonymous")
    slots: dict[str, float] = row.get("execution_slots") or {}
    if uid in slots:
        del slots[uid]
        row["reserved_notional_usd"] = max(
            0.0, float(row.get("reserved_notional_usd") or 0) - float(amount_usd)
        )


def prepare_free_telegram_batch(subscribers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Cap free Telegram blast to avoid herd triggering on identical signal."""
    max_batch = int(getattr(config, "FLYWHEEL_MAX_FREE_TELEGRAM_BATCH", 25))
    if not _enabled() or len(subscribers) <= max_batch:
        return subscribers, {"capped": False, "delivered": len(subscribers)}
    ordered = sorted(subscribers, key=lambda row: str(row.get("subscribed_at") or ""))
    capped = ordered[:max_batch]
    return capped, {"capped": True, "delivered": len(capped), "dropped": len(subscribers) - len(capped)}


def flywheel_saturation_status() -> dict[str, Any]:
    _prune_state()
    active_fps = len(_crowd_state)
    total_recipients = sum(int(v.get("alert_recipients") or 0) for v in _crowd_state.values())
    total_slots = sum(len(v.get("execution_slots") or {}) for v in _crowd_state.values())
    return {
        "enabled": _enabled(),
        "active_opportunities_tracked": active_fps,
        "blocked_alerts_total": _blocked_alerts,
        "blocked_executions_total": _blocked_executions,
        "alert_recipients_inflight": total_recipients,
        "execution_slots_inflight": total_slots,
        "max_alert_recipients": _max_alert_recipients(),
        "max_execution_slots_per_opportunity": _max_execution_slots(),
        "default_competing_notional_usd": _per_actor_notional(),
        "crowd_state_ttl_sec": _ttl_sec(),
    }
