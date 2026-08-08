"""
BLACKDARK — Telegram monitor (fast path).

Runs free + admin alerts when bot token is configured.
Default interval: 5s (aligned with aggregator), not 90s.
"""

from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger("BLACKDARK.TelegramMonitor")

_monitor_task: asyncio.Task | None = None


def bot_token_configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN"))


def admin_chat_configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def telegram_configured() -> bool:
    return bot_token_configured()


async def _monitor_cycle() -> None:
    from alert_service import dispatch_alert, send_telegram_message
    from database import fetch_users_with_telegram
    from scan_coordinator import get_shared_scan
    from telegram_free_alerts import dispatch_free_telegram_alerts

    if not bot_token_configured():
        return

    scan = await get_shared_scan(profitable_only=True, prefer_live=False)
    free_stats = await dispatch_free_telegram_alerts(scan=scan)
    if free_stats.get("sent"):
        logger.info(
            "Telegram free alerts | sent=%s skipped=%s subscribers=%s",
            free_stats.get("sent"),
            free_stats.get("skipped"),
            free_stats.get("subscribers"),
        )

    if not admin_chat_configured():
        return

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
                await send_telegram_message(f"{title}\n\n{body}", chat_id=chat_id)


async def _monitor_loop(interval_seconds: float) -> None:
    logger.info("Telegram monitor started | interval=%.1fs", interval_seconds)
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
    if not enabled or not bot_token_configured():
        logger.info(
            "Telegram monitor skipped | enabled=%s token=%s",
            enabled,
            bot_token_configured(),
        )
        return None
    if _monitor_task is not None and not _monitor_task.done():
        return _monitor_task
    interval = float(os.getenv("TELEGRAM_ALERT_INTERVAL_SECONDS", "5"))
    _monitor_task = asyncio.create_task(_monitor_loop(interval), name="telegram-monitor")
    return _monitor_task


async def stop_telegram_monitor() -> None:
    global _monitor_task
    if _monitor_task is not None:
        _monitor_task.cancel()
        await asyncio.gather(_monitor_task, return_exceptions=True)
        _monitor_task = None


async def send_test_telegram(chat_id: str | None = None) -> dict:
    from alert_service import send_telegram_message

    text = "✅ BLACKDARK Telegram alerts are live.\nYou will receive arbitrage + oracle signals here."
    ok = await send_telegram_message(text, chat_id=chat_id)
    return {
        "success": ok,
        "configured": bot_token_configured(),
        "message": "Test sent" if ok else "Failed — check TELEGRAM_BOT_TOKEN and chat_id",
    }
