"""
BLACKDARK — Telegram monitor (fast path).

Runs free + admin alerts when bot token is configured.
Default interval: 5s (aligned with aggregator), not 90s.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("BLACKDARK.TelegramMonitor")

_monitor_task: asyncio.Task | None = None
_ROOT = Path(__file__).resolve().parent
ONCALL_EVIDENCE_DEFAULT = _ROOT / "docs" / "dd" / "BLACKDARK_TELEGRAM_ONCALL_EVIDENCE.json"


def oncall_evidence_path() -> Path:
    override = os.getenv("TELEGRAM_ONCALL_EVIDENCE_PATH", "").strip()
    return Path(override) if override else ONCALL_EVIDENCE_DEFAULT


def oncall_live_proved() -> bool:
    path = oncall_evidence_path()
    if not path.is_file():
        return False
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    mid = body.get("message_id")
    return (
        body.get("verdict") == "PASS"
        and bool(body.get("ok"))
        and body.get("telegram_ok") is True
        and isinstance(mid, int)
        and mid > 0
        and bool(body.get("bot_username"))
    )

logger = logging.getLogger("BLACKDARK.TelegramMonitor")

_monitor_task: asyncio.Task | None = None


def bot_token_configured() -> bool:
    try:
        from env_secrets_loader import ensure_telegram_env

        ensure_telegram_env()
    except Exception:
        logger.debug("telegram_secrets_load_skipped", exc_info=True)
    return bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())


def admin_chat_configured() -> bool:
    try:
        from env_secrets_loader import ensure_telegram_env

        ensure_telegram_env()
    except Exception:
        logger.debug("telegram_secrets_load_skipped", exc_info=True)
    return bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip() and os.getenv("TELEGRAM_CHAT_ID", "").strip())


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


def start_telegram_monitor() -> asyncio.Task | None:
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
    from alert_service import send_telegram_message_receipt

    text = "✅ BLACKDARK Telegram alerts are live.\nYou will receive arbitrage + oracle signals here."
    receipt = await send_telegram_message_receipt(text, chat_id=chat_id)
    ok = bool(receipt.get("ok") and receipt.get("message_id"))
    return {
        "success": ok,
        "configured": bot_token_configured(),
        "message": "Test sent" if ok else "Failed — check TELEGRAM_BOT_TOKEN and chat_id",
        "message_id": receipt.get("message_id"),
        "http_status": receipt.get("http_status"),
        "reason": receipt.get("reason"),
    }


async def prove_telegram_oncall_page(*, text: str) -> dict:
    """Live on-call page: getMe + sendMessage. Secret-free receipt only."""
    from alert_service import _telegram_api, send_telegram_message_receipt, telegram_secret_presence

    presence = telegram_secret_presence()
    if not presence.get("oncall_configured"):
        return {
            "ok": False,
            "reason": "secrets_missing",
            "bot_username": None,
            "message_id": None,
            "chat_type": None,
            "http_status": 0,
            **presence,
        }
    me = await _telegram_api("getMe")
    if not me.get("ok") or not me.get("bot_username"):
        return {
            "ok": False,
            "reason": "getMe_failed",
            "bot_username": me.get("bot_username"),
            "message_id": None,
            "chat_type": None,
            "http_status": me.get("http_status") or 0,
            "error_code": me.get("error_code"),
            **presence,
        }
    send = await send_telegram_message_receipt(text)
    ok = bool(send.get("ok") and send.get("message_id") and send.get("telegram_ok") is True)
    return {
        "ok": ok,
        "reason": "ok" if ok else (send.get("reason") or "send_failed"),
        "bot_username": me.get("bot_username"),
        "message_id": send.get("message_id"),
        "chat_type": send.get("chat_type"),
        "http_status": send.get("http_status") or 0,
        "telegram_ok": send.get("telegram_ok"),
        "error_code": send.get("error_code"),
        **presence,
    }
