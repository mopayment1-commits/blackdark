"""
BLACKDARK — Background Telegram alert monitor (Week 2).

Periodically scans arbitrage + high-score oracle moves and dispatches Telegram.
"""

from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger("BLACKDARK.TelegramMonitor")

_monitor_task: asyncio.Task | None = None


def telegram_configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


async def _monitor_cycle() -> None:
    from alert_service import dispatch_alert
    from arbitrage_service import scan_arbitrage_opportunities
    from database import fetch_users_with_telegram
    from telegram_free_alerts import dispatch_free_telegram_alerts

    if not telegram_configured():
        return

    free_stats = await dispatch_free_telegram_alerts()
    if free_stats.get("sent"):
        logger.info(
            "Free Telegram alerts sent | sent=%s skipped=%s subscribers=%s",
            free_stats.get("sent"),
            free_stats.get("skipped"),
            free_stats.get("subscribers"),
        )

    scan = await scan_arbitrage_opportunities(prefer_live=True, profitable_only=True)
    top = scan.get("top_opportunity")
    if top and float(top.get("net_profit_usdt") or 0) > 0:
        title = (
            f"⚡ {top.get('kind_label')} · {top.get('asset')} · "
            f"+${float(top.get('net_profit_usdt') or 0):.2f}"
        )
        body = (
            f"Profit: {float(top.get('net_profit_percent') or 0):.3f}%\n"
            f"Feasibility: {top.get('execution_feasibility')}\n"
            f"{top.get('why', '')[:180]}"
        )
        await dispatch_alert(title, body, payload=top, channels=["telegram"])

        for row in await fetch_users_with_telegram():
            chat_id = str(row.get("telegram_chat_id") or "")
            if chat_id:
                from alert_service import send_telegram_message

                await send_telegram_message(f"{title}\n\n{body}", chat_id=chat_id)


async def _monitor_loop(interval_seconds: int = 90) -> None:
    logger.info("Telegram alert monitor started | interval=%ss", interval_seconds)
    while True:
        try:
            await _monitor_cycle()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Telegram monitor cycle failed")
        await asyncio.sleep(interval_seconds)


async def start_telegram_monitor() -> asyncio.Task | None:
    global _monitor_task
    enabled = os.getenv("TELEGRAM_ALERTS_ENABLED", "true").lower() in {"1", "true", "yes"}
    if not enabled or not telegram_configured():
        logger.info(
            "Telegram monitor skipped | enabled=%s configured=%s",
            enabled,
            telegram_configured(),
        )
        return None
    if _monitor_task is not None and not _monitor_task.done():
        return _monitor_task
    interval = int(os.getenv("TELEGRAM_ALERT_INTERVAL_SECONDS", "90"))
    _monitor_task = asyncio.create_task(_monitor_loop(interval))
    return _monitor_task


async def stop_telegram_monitor() -> None:
    global _monitor_task
    if _monitor_task is not None:
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
        _monitor_task = None


async def send_test_telegram(chat_id: str | None = None) -> dict:
    from alert_service import send_telegram_message

    text = "✅ BLACKDARK Telegram alerts are live.\nYou will receive arbitrage + oracle signals here."
    ok = await send_telegram_message(text, chat_id=chat_id)
    return {
        "success": ok,
        "configured": telegram_configured(),
        "message": "Test sent" if ok else "Failed — check TELEGRAM_BOT_TOKEN and chat_id",
    }
