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

_TELEGRAM_API = "https://api.telegram.org"


def telegram_secret_presence() -> dict[str, bool]:
    """Presence flags only. Never returns secret values."""
    try:
        from env_secrets_loader import ensure_telegram_env

        ensure_telegram_env()
    except Exception:
        logger.debug("telegram_secrets_load_skipped", exc_info=True)
    token = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
    chat = bool(os.getenv("TELEGRAM_CHAT_ID", "").strip())
    return {
        "bot_token_present": token,
        "chat_id_present": chat,
        "oncall_configured": bool(token and chat),
    }


def _telegram_credentials() -> tuple[str, str]:
    try:
        from env_secrets_loader import ensure_telegram_env

        ensure_telegram_env()
    except Exception:
        logger.debug("telegram_secrets_load_skipped", exc_info=True)
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip(), os.getenv("TELEGRAM_CHAT_ID", "").strip()


def _safe_telegram_receipt(
    *,
    ok: bool,
    reason: str,
    http_status: int = 0,
    telegram_ok: bool | None = None,
    message_id: int | None = None,
    chat_type: str | None = None,
    bot_username: str | None = None,
    error_code: int | None = None,
) -> dict[str, Any]:
    """Receipt for on-call proof. Never includes token, chat_id, or API URLs."""
    return {
        "ok": bool(ok),
        "reason": reason,
        "http_status": int(http_status or 0),
        "telegram_ok": telegram_ok,
        "message_id": message_id,
        "chat_type": chat_type,
        "bot_username": bot_username,
        "error_code": error_code,
        **telegram_secret_presence(),
    }


async def _telegram_api(method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    token, _chat = _telegram_credentials()
    if not token:
        return _safe_telegram_receipt(ok=False, reason="secrets_missing")
    # Token is only used to build the request URL; never log the URL.
    url = f"{_TELEGRAM_API}/bot{token}/{method}"
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if payload is None:
                async with session.get(url) as resp:
                    http_status = int(resp.status)
                    try:
                        body = await resp.json(content_type=None)
                    except Exception:
                        body = {}
            else:
                async with session.post(url, json=payload) as resp:
                    http_status = int(resp.status)
                    try:
                        body = await resp.json(content_type=None)
                    except Exception:
                        body = {}
    except (aiohttp.ClientError, TypeError, ValueError, OSError):
        logger.warning("telegram_api_failed method=%s reason=network", method)
        return _safe_telegram_receipt(ok=False, reason="network", http_status=0)

    if not isinstance(body, dict):
        body = {}
    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    error_code = body.get("error_code") if isinstance(body.get("error_code"), int) else None
    raw_ok = body.get("ok")
    telegram_ok = True if raw_ok is True else (False if raw_ok is False else None)
    message_id = result.get("message_id") if isinstance(result.get("message_id"), int) else None
    chat = result.get("chat") if isinstance(result.get("chat"), dict) else {}
    chat_type = chat.get("type") if isinstance(chat.get("type"), str) else None
    if not chat_type and method == "getChat" and isinstance(result.get("type"), str):
        chat_type = result.get("type")
    username = None
    if method == "getMe" and isinstance(result.get("username"), str):
        username = result.get("username").lstrip("@")
    if http_status == 200 and telegram_ok is True:
        reason = "ok"
    elif http_status == 200 and telegram_ok is None:
        reason = "http_200_no_json"
    else:
        reason = "telegram_reject"
    return _safe_telegram_receipt(
        ok=bool(telegram_ok is True and http_status == 200),
        reason=reason,
        http_status=http_status,
        telegram_ok=telegram_ok,
        message_id=message_id,
        chat_type=chat_type,
        bot_username=username,
        error_code=error_code,
    )


async def send_telegram_message_receipt(text: str, chat_id: str | None = None) -> dict[str, Any]:
    """Send via Bot API sendMessage and return a secret-free receipt."""
    token, default_chat = _telegram_credentials()
    target = (chat_id or default_chat or "").strip()
    if not token or not target:
        return _safe_telegram_receipt(ok=False, reason="secrets_missing")
    receipt = await _telegram_api(
        "sendMessage",
        {"chat_id": target, "text": text, "parse_mode": "HTML"},
    )
    return receipt


async def send_telegram_message(text: str, chat_id: str | None = None) -> bool:
    receipt = await send_telegram_message_receipt(text, chat_id=chat_id)
    if receipt.get("reason") == "secrets_missing":
        return False
    if receipt.get("telegram_ok") is False or receipt.get("error_code"):
        return False
    if receipt.get("http_status") == 200:
        return True
    return bool(receipt.get("ok"))


def send_email_alert(to_email: str, subject: str, body: str) -> bool:
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
    """Click-to-send deep link (always available)."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"https://wa.me/{digits}?text={quote(text)}"


def whatsapp_cloud_configured() -> bool:
    return bool(
        os.getenv("WHATSAPP_CLOUD_TOKEN", "").strip()
        and os.getenv("WHATSAPP_CLOUD_PHONE_NUMBER_ID", "").strip()
    )


async def send_whatsapp_cloud_message(phone: str, text: str) -> bool:
    """
    WhatsApp Cloud API push when WHATSAPP_CLOUD_TOKEN + WHATSAPP_CLOUD_PHONE_NUMBER_ID set.
    Completes the product path — no deferred WhatsApp channel in code.
    """
    token = os.getenv("WHATSAPP_CLOUD_TOKEN", "").strip()
    phone_id = os.getenv("WHATSAPP_CLOUD_PHONE_NUMBER_ID", "").strip()
    if not token or not phone_id:
        return False
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not digits:
        return False
    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": digits,
        "type": "text",
        "text": {"body": text[:4000]},
    }
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            url, headers=headers, json=payload
        ) as resp:
            return resp.status in (200, 201)
    except (aiohttp.ClientError, TypeError, ValueError):
        logger.exception("WhatsApp Cloud delivery failed")
        return False


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
    ina = push_in_app_alert(title, body, payload=payload, level="signal")
    results["channels"]["in_app"] = True
    results["in_app_id"] = ina.get("id")

    await _dispatch_global_channels(channels, full_text, results)

    subs = await fetch_active_alert_subscriptions()
    for sub in subs:
        sub_result = await _dispatch_subscription_alert(sub, title, body, full_text, payload, results)
        results["subscriptions"].append(sub_result)

    await insert_alert_delivery_log(title, json.dumps(payload or {}), json.dumps(results))
    return results


async def _dispatch_global_channels(channels: list[str], full_text: str, results: dict[str, Any]) -> None:
    if "telegram" in channels:
        token_ok = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
        if not token_ok:
            results["channels"]["telegram"] = False
            results["telegram_status"] = "skipped_no_token"
        else:
            results["channels"]["telegram"] = await send_telegram_message(full_text)

    if "email" in channels and not os.getenv("SMTP_HOST", "").strip():
        results["channels"]["email"] = False
        results["email_status"] = "queued_durable_outbox"


async def _dispatch_subscription_alert(
    sub: dict[str, Any],
    title: str,
    body: str,
    full_text: str,
    payload: dict[str, Any] | None,
    results: dict[str, Any],
) -> dict[str, Any]:
    from in_app_alerts import push_in_app_alert

    sub_result: dict[str, Any] = {"id": sub.get("id")}
    email = sub.get("email")
    if email and sub.get("email_alerts", 1):
        if not os.getenv("SMTP_HOST", "").strip():
            from email_outbox import enqueue_email

            queued = enqueue_email(str(email), title, full_text, payload=payload)
            sub_result["email"] = False
            sub_result["email_status"] = "queued_durable_outbox"
            sub_result["outbox_id"] = queued.get("id")
            push_in_app_alert(title, body, payload=payload, user_email=str(email), level="signal")
        else:
            sub_result["email"] = send_email_alert(email, title, full_text)
    tg_chat = sub.get("telegram_chat_id")
    if tg_chat:
        sub_result["telegram"] = await send_telegram_message(full_text, chat_id=tg_chat)
    wa_phone = sub.get("whatsapp_phone")
    if wa_phone and sub.get("whatsapp_alerts", 1):
        sub_result["whatsapp_url"] = whatsapp_alert_url(wa_phone, full_text)
        if whatsapp_cloud_configured():
            sub_result["whatsapp_cloud"] = await send_whatsapp_cloud_message(wa_phone, full_text)
            results["channels"]["whatsapp_cloud"] = bool(sub_result["whatsapp_cloud"])
        else:
            sub_result["whatsapp_mode"] = "click_to_send_wa_me"
            results["channels"]["whatsapp"] = "click_to_send"
    return sub_result


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

    wa_url = whatsapp_alert_url(whatsapp_phone, "BLACKDARK alerts ready.") if whatsapp_phone else None
    return {
        "success": True,
        "subscription_id": sub_id,
        "telegram_welcome_sent": welcome_sent,
        "whatsapp_url": wa_url,
        "whatsapp_cloud_ready": whatsapp_cloud_configured(),
        "message": "Alert subscription saved.",
        "channels_complete": {
            "telegram": bool(telegram_chat_id),
            "email": bool(email),
            "whatsapp_click_to_send": bool(whatsapp_phone),
            "whatsapp_cloud_push": whatsapp_cloud_configured(),
            "in_app": True,
        },
    }


async def send_test_alert(email: str | None = None) -> dict[str, Any]:
    return await dispatch_alert(
        "BLACKDARK Test Alert",
        "Your alert channels are configured. You will receive oracle and arbitrage signals.",
        channels=["telegram", "email", "in_app"],
    )
