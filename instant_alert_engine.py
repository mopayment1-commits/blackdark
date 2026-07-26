"""
BLACKDARK — Instant Alert Engine.

Fast arbitrage + Oracle pulse aligned with market speed (default ~2s).
Separate from the slow Telegram broadcast loop — fires on hot opportunities only.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from typing import Any

logger = logging.getLogger("BLACKDARK.InstantAlerts")

_engine_task: asyncio.Task | None = None
_running = False
_last_fingerprint: str = ""
_last_alert_at: float = 0.0
_cooldown_cache: dict[str, float] = {}


def _enabled() -> bool:
    return os.getenv("INSTANT_ALERTS_ENABLED", "true").lower() in {"1", "true", "yes"}


def _interval_sec() -> float:
    return max(0.5, float(os.getenv("INSTANT_ALERT_INTERVAL_SEC", "2")))


def _cooldown_sec() -> float:
    return max(5.0, float(os.getenv("INSTANT_ALERT_COOLDOWN_SEC", "45")))


def _min_profit_usdt() -> float:
    return float(os.getenv("INSTANT_ALERT_MIN_PROFIT_USDT", "0.15"))


def _fingerprint(opp: dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(opp.get("kind") or ""),
            str(opp.get("asset") or ""),
            str(opp.get("buy_exchange") or opp.get("buy_venue") or ""),
            str(opp.get("sell_exchange") or opp.get("sell_venue") or ""),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _cooldown_ok(key: str) -> bool:
    now = time.monotonic()
    last = _cooldown_cache.get(key, 0.0)
    if now - last < _cooldown_sec():
        return False
    _cooldown_cache[key] = now
    return True


async def _pulse_once() -> dict[str, Any]:
    global _last_fingerprint, _last_alert_at

    from risk_manager import is_trading_frozen

    if is_trading_frozen():
        return {"skipped": True, "reason": "trading_frozen", "interval_sec": _interval_sec()}

    from arbitrage_service import process_arbitrage_alerts
    from scan_coordinator import get_shared_scan

    started = time.monotonic()
    scan = await get_shared_scan(profitable_only=True, prefer_live=False, force_rest=False)
    elapsed_ms = round((time.monotonic() - started) * 1000, 1)

    top = scan.get("top_opportunity") or {}
    profit = float(top.get("net_profit_usdt") or 0)
    triggered: list[dict[str, Any]] = []
    telegram_sent = 0

    if top and profit >= _min_profit_usdt():
        fp = _fingerprint(top)
        if fp != _last_fingerprint and _cooldown_ok(fp):
            alerts = await process_arbitrage_alerts(scan)
            triggered.extend(alerts)
            _last_fingerprint = fp
            _last_alert_at = time.monotonic()
            telegram_sent = sum(1 for alert in alerts if alert)

            if os.getenv("AUTO_EXECUTION_LOOP", "true").lower() in {"1", "true", "yes"}:
                try:
                    from execution_engine import try_execute_from_opportunity

                    top_exec = dict(top)
                    top_exec["data_age_sec"] = scan.get("data_age_sec")
                    exec_result = await try_execute_from_opportunity(top_exec)
                    if exec_result.get("executed"):
                        logger.info(
                            "Fast execution | mode=%s asset=%s profit=$%.2f",
                            exec_result.get("mode"),
                            top.get("asset"),
                            profit,
                        )
                except Exception:
                    logger.exception("Fast execution from instant pulse failed")

    return {
        "scan_ms": elapsed_ms,
        "engine_scan_ms": scan.get("scan_ms"),
        "data_age_sec": scan.get("data_age_sec"),
        "opportunities": len(scan.get("opportunities") or []),
        "top_profit_usdt": profit,
        "alerts_triggered": len(triggered),
        "telegram_sent": telegram_sent,
        "interval_sec": _interval_sec(),
    }


async def _engine_loop() -> None:
    logger.info(
        "Instant alert engine started | interval=%.1fs cooldown=%.0fs",
        _interval_sec(),
        _cooldown_sec(),
    )
    while _running:
        try:
            stats = await _pulse_once()
            if stats.get("alerts_triggered") or stats.get("telegram_sent"):
                logger.info(
                    "Instant pulse | scan_ms=%s profit=$%.2f alerts=%s telegram=%s",
                    stats.get("scan_ms"),
                    stats.get("top_profit_usdt"),
                    stats.get("alerts_triggered"),
                    stats.get("telegram_sent"),
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Instant alert pulse failed")
        await asyncio.sleep(_interval_sec())


async def start_instant_alert_engine() -> asyncio.Task | None:
    global _running, _engine_task
    if not _enabled():
        logger.info("Instant alert engine disabled (INSTANT_ALERTS_ENABLED=false)")
        return None
    if _engine_task is not None and not _engine_task.done():
        return _engine_task
    _running = True
    _engine_task = asyncio.create_task(_engine_loop(), name="instant-alerts")
    return _engine_task


async def stop_instant_alert_engine() -> None:
    global _running, _engine_task
    _running = False
    if _engine_task is not None:
        _engine_task.cancel()
        try:
            await _engine_task
        except asyncio.CancelledError:
            pass
        _engine_task = None
    logger.info("Instant alert engine stopped.")


def engine_stats() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "running": _running,
        "interval_sec": _interval_sec(),
        "cooldown_sec": _cooldown_sec(),
        "last_fingerprint": _last_fingerprint or None,
        "last_alert_age_sec": round(time.monotonic() - _last_alert_at, 1) if _last_alert_at else None,
    }
