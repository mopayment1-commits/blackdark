"""Telegram bot webhook and free alerts API."""

from __future__ import annotations

import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, Request

from security_auth import require_admin

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram Bot API webhook — /start subscribes to 3 free alerts/day."""
    from security_auth import is_production_env

    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not secret:
        if is_production_env():
            raise HTTPException(
                status_code=503,
                detail="TELEGRAM_WEBHOOK_SECRET required in production",
            )
    else:
        provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(provided, secret):
            raise HTTPException(status_code=403, detail="Invalid webhook secret")
    from alert_service import send_telegram_message
    from telegram_free_alerts import handle_bot_command

    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = str(message.get("text") or "").strip()
    username = chat.get("username")

    if not chat_id or not text:
        return {"ok": True}

    if text.startswith("/"):
        reply = await handle_bot_command(str(chat_id), text, username=username)
        if reply:
            await send_telegram_message(reply, chat_id=str(chat_id))
    return {"ok": True}


@router.get("/free/status")
async def telegram_free_status():
    from database import count_telegram_free_subscribers
    from telegram_free_alerts import FREE_DAILY_ALERT_LIMIT

    return {
        "enabled": os.getenv("TELEGRAM_FREE_ALERTS_ENABLED", "true").lower() in {"1", "true", "yes"},
        "daily_limit": FREE_DAILY_ALERT_LIMIT,
        "active_subscribers": await count_telegram_free_subscribers(),
        "bot_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "bot_username": os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@"),
        "commands": ["/start", "/stop", "/status", "/accuracy"],
    }


@router.post("/free/broadcast")
async def telegram_free_broadcast(_admin: dict = Depends(require_admin)):
    from telegram_free_alerts import dispatch_free_telegram_alerts

    return await dispatch_free_telegram_alerts()
