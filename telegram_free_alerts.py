"""
BLACKDARK — Free Telegram Alerts (Launch Growth).

Public bot subscriptions with 3 alerts/day per user.
/start auto-subscribes · /stop unsubscribes · /status · /accuracy
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.TelegramFree")

FREE_DAILY_ALERT_LIMIT = int(os.getenv("TELEGRAM_FREE_DAILY_LIMIT", "3"))


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _today_key() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


async def subscribe_free_chat(chat_id: str, *, username: str | None = None) -> dict[str, Any]:
    from database import upsert_telegram_free_subscriber

    row = await upsert_telegram_free_subscriber(
        chat_id=str(chat_id),
        username=username,
        enabled=True,
    )
    return {
        "subscribed": True,
        "chat_id": str(chat_id),
        "daily_limit": FREE_DAILY_ALERT_LIMIT,
        "tier": "free",
        "row": row,
    }


async def unsubscribe_free_chat(chat_id: str) -> dict[str, Any]:
    from database import set_telegram_free_subscriber_enabled

    await set_telegram_free_subscriber_enabled(str(chat_id), enabled=False)
    return {"subscribed": False, "chat_id": str(chat_id)}


async def free_subscriber_status(chat_id: str) -> dict[str, Any]:
    from database import fetch_telegram_free_subscriber

    row = await fetch_telegram_free_subscriber(str(chat_id))
    if not row or not row.get("enabled"):
        return {
            "subscribed": False,
            "chat_id": str(chat_id),
            "daily_limit": FREE_DAILY_ALERT_LIMIT,
            "alerts_sent_today": 0,
            "alerts_remaining_today": FREE_DAILY_ALERT_LIMIT,
        }
    usage_date = str(row.get("usage_date") or "")
    sent_today = int(row.get("alerts_today") or 0)
    if usage_date != _today_key():
        sent_today = 0
    remaining = max(0, FREE_DAILY_ALERT_LIMIT - sent_today)
    return {
        "subscribed": True,
        "chat_id": str(chat_id),
        "username": row.get("username"),
        "daily_limit": FREE_DAILY_ALERT_LIMIT,
        "alerts_sent_today": sent_today,
        "alerts_remaining_today": remaining,
        "subscribed_at": row.get("subscribed_at"),
    }


async def can_send_free_alert(chat_id: str) -> bool:
    status = await free_subscriber_status(chat_id)
    return bool(status.get("subscribed")) and int(status.get("alerts_remaining_today") or 0) > 0


async def record_free_alert_sent(chat_id: str) -> None:
    from database import increment_telegram_free_alert_usage

    await increment_telegram_free_alert_usage(str(chat_id), _today_key(), FREE_DAILY_ALERT_LIMIT)


async def build_accuracy_message() -> str:
    try:
        from ml.public_accuracy import build_public_accuracy_payload

        payload = await build_public_accuracy_payload(recent_limit=3)
        oracle = payload.get("oracle") or {}
        model = payload.get("model") or {}
        return (
            "📊 <b>BLACKDARK Oracle Accuracy</b>\n\n"
            f"Average accuracy: <b>{float(oracle.get('average_accuracy_percent') or 0):.1f}%</b>\n"
            f"Total predictions: <b>{oracle.get('total_predictions') or 0}</b>\n"
            f"Resolved: <b>{oracle.get('resolved_predictions') or 0}</b>\n"
            f"Training samples: <b>{model.get('labeled_samples') or 0}</b>\n\n"
            "🔗 Live page: /oracle-accuracy"
        )
    except Exception:
        return "📊 Oracle accuracy warming up — check back soon at /oracle-accuracy"


async def handle_bot_command(
    chat_id: str,
    text: str,
    *,
    username: str | None = None,
) -> str | None:
    """Return reply text for a Telegram command (HTML)."""
    command = text.strip().split()[0].lower()
    if command.startswith("/start"):
        await subscribe_free_chat(chat_id, username=username)
        return (
            "✅ <b>Welcome to BLACKDARK Free Alerts</b>\n\n"
            "You are subscribed to <b>3 free AI signals per day</b>:\n"
            "• Top arbitrage opportunities\n"
            "• High-score Oracle moves\n\n"
            "<b>Commands</b>\n"
            "/status — your daily quota\n"
            "/accuracy — live Oracle accuracy\n"
            "/stop — unsubscribe\n\n"
            f"Your chat ID: <code>{chat_id}</code>"
        )
    if command.startswith("/stop"):
        await unsubscribe_free_chat(chat_id)
        return "🛑 Unsubscribed from free alerts. Send /start anytime to rejoin."
    if command.startswith("/status"):
        status = await free_subscriber_status(chat_id)
        if not status.get("subscribed"):
            return "You are not subscribed. Send /start to get 3 free alerts/day."
        return (
            "📡 <b>Free Alert Status</b>\n\n"
            f"Sent today: <b>{status.get('alerts_sent_today')}</b> / {FREE_DAILY_ALERT_LIMIT}\n"
            f"Remaining: <b>{status.get('alerts_remaining_today')}</b>"
        )
    if command.startswith("/accuracy"):
        return await build_accuracy_message()
    return None


async def dispatch_free_telegram_alerts(*, scan: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send launch alerts to all free subscribers within daily quota."""
    import asyncio

    from alert_service import send_telegram_message
    from database import fetch_enabled_telegram_free_subscribers
    from scan_coordinator import get_shared_scan

    subscribers = await fetch_enabled_telegram_free_subscribers()
    if not subscribers:
        return {"sent": 0, "skipped": 0, "reason": "no_subscribers"}

    if scan is None:
        scan = await get_shared_scan(profitable_only=True, prefer_live=False)
    top = scan.get("top_opportunity")
    messages: list[str] = []

    if top and float(top.get("net_profit_usdt") or 0) > 0:
        messages.append(
            "⚡ <b>BLACKDARK Free Alert</b>\n\n"
            f"{top.get('kind_label')} · <b>{top.get('asset')}</b>\n"
            f"Profit: <b>+${float(top.get('net_profit_usdt') or 0):.2f}</b> "
            f"({float(top.get('net_profit_percent') or 0):.3f}%)\n"
            f"Feasibility: {top.get('execution_feasibility')}\n"
            f"{str(top.get('why') or '')[:160]}"
        )

    try:
        from database import fetch_evaluated_opportunities

        rows = await fetch_evaluated_opportunities(limit=20)
        oracle_rows = [
            row for row in rows if int(row.get("opportunity_score") or 0) >= 70
        ]
        if oracle_rows:
            row = oracle_rows[0]
            messages.append(
                "🧠 <b>Oracle Signal</b>\n\n"
                f"Asset: <b>{row.get('asset')}</b>\n"
                f"Verdict: <b>{row.get('oracle_verdict')}</b>\n"
                f"Score: <b>{row.get('opportunity_score')}</b>\n"
                f"{str(row.get('oracle_sentence') or '')[:160]}"
            )
    except Exception:
        logger.debug("optional operation skipped", exc_info=True)

    if not messages:
        messages.append(
            "🔔 <b>BLACKDARK Market Scan</b>\n\n"
            "No high-priority opportunity this cycle.\n"
            "Track live Oracle accuracy: /accuracy"
        )

    sent = 0
    skipped = 0
    sem = asyncio.Semaphore(10)

    async def _deliver(subscriber: dict[str, Any]) -> str:
        chat_id = str(subscriber.get("chat_id") or "")
        if not chat_id:
            return "skip"
        if not await can_send_free_alert(chat_id):
            return "skip"
        body = messages[0]
        async with sem:
            ok = await send_telegram_message(body, chat_id=chat_id)
        if ok:
            await record_free_alert_sent(chat_id)
            return "sent"
        return "skip"

    results = await asyncio.gather(*[_deliver(subscriber) for subscriber in subscribers])
    sent = sum(1 for result in results if result == "sent")
    skipped = len(subscribers) - sent

    return {
        "sent": sent,
        "skipped": skipped,
        "subscribers": len(subscribers),
        "messages_prepared": len(messages),
    }
