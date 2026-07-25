"""
BLACKDARK — Telegram long-polling for local/dev (no webhook required).

Set TELEGRAM_POLLING_ENABLED=true when TELEGRAM_BOT_TOKEN is set.
"""

from __future__ import annotations

import asyncio
import logging
import os

import aiohttp

logger = logging.getLogger("BLACKDARK.TelegramPoller")

_poller_task: asyncio.Task | None = None
_offset: int = 0


async def _poll_once(token: str) -> None:
    global _offset
    from alert_service import send_telegram_message
    from telegram_free_alerts import handle_bot_command

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"timeout": 20, "offset": _offset + 1}
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return
            payload = await resp.json()

    for update in payload.get("result") or []:
        _offset = max(_offset, int(update.get("update_id") or 0))
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = str(message.get("text") or "").strip()
        if not chat_id or not text.startswith("/"):
            continue
        reply = await handle_bot_command(str(chat_id), text, username=chat.get("username"))
        if reply:
            await send_telegram_message(reply, chat_id=str(chat_id))


async def _poll_loop() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return
    logger.info("Telegram polling started (dev mode)")
    while True:
        try:
            await _poll_once(token)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Telegram polling failed")
        await asyncio.sleep(1)


async def start_telegram_poller() -> asyncio.Task | None:
    global _poller_task
    enabled = os.getenv("TELEGRAM_POLLING_ENABLED", "false").lower() in {"1", "true", "yes"}
    if not enabled or not os.getenv("TELEGRAM_BOT_TOKEN"):
        return None
    if _poller_task is not None and not _poller_task.done():
        return _poller_task
    _poller_task = asyncio.create_task(_poll_loop(), name="telegram-poller")
    return _poller_task


async def stop_telegram_poller() -> None:
    global _poller_task
    if _poller_task is not None:
        _poller_task.cancel()
        try:
            await _poller_task
        except asyncio.CancelledError:
            pass
        _poller_task = None
