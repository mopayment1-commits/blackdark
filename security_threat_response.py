"""Failed-login tracking, IP blocks, and instant security alerts (email + Telegram)."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request

logger = logging.getLogger("BLACKDARK.ThreatResponse")

_FAIL_WINDOW_SEC = int(os.getenv("LOGIN_FAIL_WINDOW_SEC", "900"))
_FAIL_MAX = int(os.getenv("LOGIN_FAIL_MAX", "5"))
_IP_BLOCK_SEC = int(os.getenv("LOGIN_IP_BLOCK_SEC", "900"))

_failures_by_ip: dict[str, list[float]] = defaultdict(list)
_blocked_ips: dict[str, float] = {}
_ALERT_COOLDOWN_SEC = 300
_last_alert: dict[str, float] = {}


def client_ip(request: Request | None) -> str:
    if request is None:
        return "unknown"
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


def client_user_agent(request: Request | None) -> str:
    if request is None:
        return ""
    return (request.headers.get("user-agent") or "")[:512]


def client_country(request: Request | None) -> str | None:
    if request is None:
        return None
    for header in ("cf-ipcountry", "x-vercel-ip-country", "x-country-code"):
        val = (request.headers.get(header) or "").strip().upper()
        if val and val not in {"XX", "T1"}:
            return val
    return None


def assert_ip_not_blocked(request: Request | None) -> None:
    ip = client_ip(request)
    now = time.time()
    exp = _blocked_ips.get(ip)
    if exp and exp > now:
        raise HTTPException(
            status_code=403,
            detail={"error": "ip_temporarily_blocked", "retry_after_sec": int(exp - now)},
        )
    if exp:
        _blocked_ips.pop(ip, None)


def _block_ip(ip: str) -> None:
    _blocked_ips[ip] = time.time() + _IP_BLOCK_SEC


def _prune_failures(ip: str, now: float) -> list[float]:
    window = [t for t in _failures_by_ip[ip] if now - t < _FAIL_WINDOW_SEC]
    _failures_by_ip[ip] = window
    return window


async def _send_security_alert(subject: str, body: str) -> None:
    from security_auth import admin_emails

    emails = sorted(admin_emails())
    target = (os.getenv("SECURITY_ALERT_EMAIL") or "").strip().lower()
    if target and target not in emails:
        emails.insert(0, target)
    for addr in emails[:3]:
        try:
            from alert_service import send_email_alert

            send_email_alert(addr, subject, body)
        except Exception:
            logger.debug("security email alert failed", exc_info=True)
    chat = (
        os.getenv("SECURITY_TELEGRAM_CHAT_ID")
        or os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        or os.getenv("TELEGRAM_ALERT_CHAT_ID")
        or ""
    ).strip()
    if chat:
        try:
            from alert_service import send_telegram_message

            await send_telegram_message(body[:3500], chat_id=chat)
        except Exception:
            logger.debug("security telegram alert failed", exc_info=True)


def _alert_throttled(key: str) -> bool:
    now = time.time()
    last = _last_alert.get(key, 0.0)
    if now - last < _ALERT_COOLDOWN_SEC:
        return True
    _last_alert[key] = now
    return False


async def record_failed_login(
    *,
    request: Request | None,
    email: str | None = None,
    reason: str = "invalid_credentials",
) -> None:
    from security_events import record_security_event

    ip = client_ip(request)
    ua = client_user_agent(request)
    now = time.time()
    window = _prune_failures(ip, now)
    window.append(now)
    _failures_by_ip[ip] = window

    record_security_event(
        "login_failure",
        severity="warning",
        actor=email,
        ip=ip,
        detail={"reason": reason, "user_agent": ua},
    )

    if len(window) >= _FAIL_MAX:
        _block_ip(ip)
        if not _alert_throttled(f"fail:{ip}"):
            await _send_security_alert(
                "[BLACKDARK] Login brute-force threshold",
                f"IP {ip} blocked after {len(window)} failed logins in {_FAIL_WINDOW_SEC}s.\n"
                f"Last email tried: {email or 'n/a'}\nUA: {ua}",
            )


async def record_successful_login(
    *,
    request: Request | None,
    user_id: int,
    email: str,
) -> None:
    from security_events import record_security_event
    from security_store import record_login_fingerprint

    fp = await record_login_fingerprint(
        user_id,
        user_agent=client_user_agent(request),
        country=client_country(request),
    )
    record_security_event(
        "login_success",
        severity="info",
        actor=email,
        ip=client_ip(request),
        detail=fp,
    )
    if fp.get("is_new_device") or fp.get("is_new_country"):
        key = f"login:{user_id}:{fp.get('device_hash')}"
        if not _alert_throttled(key):
            label = "new device" if fp.get("is_new_device") else "new country"
            await _send_security_alert(
                f"[BLACKDARK] Login from {label}",
                f"User {email} signed in from {label}.\n"
                f"Country: {fp.get('country') or 'unknown'}\n"
                f"IP: {client_ip(request)}\n"
                f"UA: {client_user_agent(request)[:200]}",
            )


async def record_admin_access_denied(request: Request | None, *, detail: str) -> None:
    from security_events import record_security_event

    ip = client_ip(request)
    record_security_event(
        "admin_access_denied",
        severity="warning",
        ip=ip,
        detail={"message": detail, "user_agent": client_user_agent(request), "path": getattr(request.url, "path", "") if request else ""},
    )
    if not _alert_throttled(f"admin:{ip}"):
        await _send_security_alert(
            "[BLACKDARK] Admin access denied",
            f"Unauthorized admin attempt from {ip}.\n{detail}",
        )


def schedule_security_task(coro) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
