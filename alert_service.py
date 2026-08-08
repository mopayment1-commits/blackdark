"""
BLACKDARK — Unified Alert Service (Wave 4B).

Telegram, Email, and WhatsApp (click-to-send) delivery for oracle and arbitrage signals.
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import Any
from urllib.parse import quote

import aiohttp

logger = logging.getLogger("BLACKDARK.AlertService")


async def send_telegram_message(text: str, chat_id: str | None = None) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    target = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not target:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": target, "text": text, "parse_mode": "HTML"}
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                return resp.status == 200
    except (aiohttp.ClientError, TypeError, ValueError):
        logger.exception("Telegram delivery failed")
        return False


async def send_email_alert(to_email: str, subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", user or "alerts@blackdark.ai")

    if not host or not to_email:
        return False

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = to_email

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_email], message.as_string())
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception("Email delivery failed | to=%s", to_email)
        return False


def whatsapp_alert_url(phone: str, text: str) -> str:
    """Fallback click-to-chat deep link when Twilio WhatsApp is not configured."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"https://wa.me/{digits}?text={quote(text)}"


def twilio_whatsapp_configured() -> bool:
    return bool(
        os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        and os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        and os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
    )


async def send_whatsapp_twilio(phone: str, text: str) -> dict[str, Any]:
    """
    Send WhatsApp via Twilio Content API (WhatsApp Business).
    Env: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM (e.g. whatsapp:+14155238886)
    """
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_wa = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not (sid and token and from_wa and digits):
        return {"sent": False, "reason": "twilio_not_configured", "whatsapp_url": whatsapp_alert_url(phone, text)}

    to_wa = f"whatsapp:+{digits}"
    if not from_wa.startswith("whatsapp:"):
        from_wa = f"whatsapp:{from_wa}" if from_wa.startswith("+") else f"whatsapp:+{from_wa.lstrip('+')}"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = {
        "From": from_wa,
        "To": to_wa,
        "Body": text[:1500],
    }
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        auth = aiohttp.BasicAuth(sid, token)
        async with aiohttp.ClientSession(timeout=timeout, auth=auth) as session:
            async with session.post(url, data=data) as resp:
                body = await resp.text()
                if resp.status in {200, 201}:
                    return {"sent": True, "provider": "twilio", "status": resp.status}
                logger.warning("Twilio WhatsApp failed | status=%s body=%s", resp.status, body[:200])
                return {
                    "sent": False,
                    "reason": f"twilio_http_{resp.status}",
                    "whatsapp_url": whatsapp_alert_url(phone, text),
                }
    except (aiohttp.ClientError, TypeError, ValueError) as exc:
        logger.exception("Twilio WhatsApp delivery failed")
        return {
            "sent": False,
            "reason": str(exc)[:120],
            "whatsapp_url": whatsapp_alert_url(phone, text),
        }


async def dispatch_alert(
    title: str,
    body: str,
    *,
    payload: dict[str, Any] | None = None,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send alert through configured channels + always persist in-app inbox."""
    from database import fetch_active_alert_subscriptions, insert_alert_delivery_log
    from in_app_alerts import push_in_app_alert

    results: dict[str, Any] = {"title": title, "channels": {}, "subscriptions": []}
    full_text = f"{title}\n\n{body}"

    if channels is None:
        channels = ["telegram", "email", "whatsapp", "in_app"]

    # Always keep an in-app record so the product works without Telegram/SMTP
    if "in_app" in channels or True:
        ina = push_in_app_alert(title, body, payload=payload, level="signal")
        results["channels"]["in_app"] = True
        results["in_app_id"] = ina.get("id")

    if "telegram" in channels:
        token_ok = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
        if not token_ok:
            results["channels"]["telegram"] = False
            results["telegram_status"] = "skipped_no_token"
        else:
            ok = await send_telegram_message(full_text)
            results["channels"]["telegram"] = ok

    if "email" in channels and not os.getenv("SMTP_HOST", "").strip():
        results["channels"]["email"] = False
        results["email_status"] = "queued_durable_outbox"

    subs = await fetch_active_alert_subscriptions()
    for sub in subs:
        sub_result: dict[str, Any] = {"id": sub.get("id")}
        email = sub.get("email")
        if email and sub.get("email_alerts", 1):
            if not os.getenv("SMTP_HOST", "").strip():
                from email_outbox import enqueue_email

                queued = enqueue_email(str(email), title, full_text, payload=payload)
                sub_result["email"] = False
                sub_result["email_status"] = "queued_durable_outbox"
                sub_result["outbox_id"] = queued.get("id")
                push_in_app_alert(
                    title,
                    body,
                    payload=payload,
                    user_email=str(email),
                    level="signal",
                )
            else:
                sub_result["email"] = await send_email_alert(email, title, full_text)
        tg_chat = sub.get("telegram_chat_id")
        if tg_chat:
            sub_result["telegram"] = await send_telegram_message(full_text, chat_id=tg_chat)
        wa_phone = sub.get("whatsapp_phone")
        if wa_phone and sub.get("whatsapp_alerts", 1):
            if twilio_whatsapp_configured():
                wa = await send_whatsapp_twilio(str(wa_phone), full_text)
                sub_result["whatsapp"] = bool(wa.get("sent"))
                sub_result["whatsapp_provider"] = wa.get("provider") or "twilio"
                if wa.get("whatsapp_url"):
                    sub_result["whatsapp_url"] = wa["whatsapp_url"]
            else:
                sub_result["whatsapp"] = False
                sub_result["whatsapp_provider"] = "wa.me"
                sub_result["whatsapp_url"] = whatsapp_alert_url(str(wa_phone), full_text)
        results["subscriptions"].append(sub_result)

    await insert_alert_delivery_log(title, json.dumps(payload or {}), json.dumps(results))
    return results


async def subscribe_alerts(data: dict[str, Any], *, user_email: str | None = None) -> dict[str, Any]:
    from database import insert_alert_subscription, update_user_telegram_chat_id

    email = (data.get("email") or user_email or "").strip().lower() or None
    telegram_chat_id = (data.get("telegram_chat_id") or "").strip() or None
    whatsapp_phone = (data.get("whatsapp_phone") or "").strip() or None

    if not any([email, telegram_chat_id, whatsapp_phone]):
        raise ValueError("Provide at least one contact: email, telegram_chat_id, or whatsapp_phone")

    if user_email and telegram_chat_id:
        await update_user_telegram_chat_id(user_email, telegram_chat_id)

    sub_id = await insert_alert_subscription(
        email=email,
        telegram_chat_id=telegram_chat_id,
        whatsapp_phone=whatsapp_phone,
        min_profit_pct=float(data.get("min_profit_pct") or 0.05),
        oracle_alerts=bool(data.get("oracle_alerts", True)),
        arbitrage_alerts=bool(data.get("arbitrage_alerts", True)),
    )

    welcome_sent = False
    if telegram_chat_id:
        welcome_sent = await send_telegram_message(
            "✅ <b>BLACKDARK Alerts Active</b>\n"
            "You will receive arbitrage + oracle signals here.",
            chat_id=telegram_chat_id,
        )

    return {
        "success": True,
        "subscription_id": sub_id,
        "telegram_welcome_sent": welcome_sent,
        "message": "Alert subscription saved.",
    }


async def send_test_alert(email: str | None = None) -> dict[str, Any]:
    return await dispatch_alert(
        "BLACKDARK Test Alert",
        "Your alert channels are configured. You will receive oracle and arbitrage signals.",
        channels=["telegram", "email", "in_app"],
    )
