"""Signed outbound webhooks for Decision API v1 (Integration Addendum)."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import socket
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("BLACKDARK.DecisionAPIWebhooks")

ALLOWED_EVENTS: frozenset[str] = frozenset({"ping", "oracle.decision", "feed.snapshot"})
DEFAULT_EVENTS: tuple[str, ...] = ("ping", "oracle.decision")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _is_production() -> bool:
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def _blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_webhook_url(url: str) -> str:
    """HTTPS-only in production; block private/metadata addresses (SSRF)."""
    raw = (url or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if not host or parsed.scheme not in {"http", "https"}:
        raise ValueError("webhook_url_invalid")
    if parsed.username or parsed.password:
        raise ValueError("webhook_url_invalid")
    allow_http_loopback = (not _is_production()) and host in {"127.0.0.1", "localhost"}
    if parsed.scheme != "https" and not allow_http_loopback:
        raise ValueError("https_required")
    allowlist = {
        part.strip().lower()
        for part in os.getenv("DECISION_API_WEBHOOK_HOST_ALLOWLIST", "").split(",")
        if part.strip()
    }
    if allowlist and host not in allowlist and host not in {"127.0.0.1", "localhost"}:
        raise ValueError("webhook_host_not_allowlisted")
    if allow_http_loopback:
        return raw
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("webhook_host_unresolved") from exc
    if not infos:
        raise ValueError("webhook_host_unresolved")
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if _blocked_ip(ip):
            raise ValueError("webhook_host_forbidden")
    return raw


def sign_webhook_body(signing_secret: str, timestamp: str, body: str) -> str:
    mac = hmac.new(
        signing_secret.encode("utf-8"),
        f"{timestamp}.{body}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={mac}"


def verify_webhook_signature(
    *,
    signing_secret: str,
    timestamp: str,
    body: str,
    signature: str,
    max_skew_sec: int = 300,
) -> bool:
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(int(time.time()) - ts) > max_skew_sec:
        return False
    expected = sign_webhook_body(signing_secret, timestamp, body)
    return hmac.compare_digest(expected, (signature or "").strip())


def public_webhook_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("public_id"),
        "org_id": row.get("org_id"),
        "url": row.get("url"),
        "events": row.get("events") or [],
        "enabled": bool(row.get("enabled")),
        "created_at": row.get("created_at"),
        "last_status": row.get("last_status"),
        "last_delivered_at": row.get("last_delivered_at"),
    }


async def register_webhook(
    *,
    principal: dict[str, Any],
    url: str,
    events: list[str] | None,
) -> dict[str, Any]:
    from database import insert_decision_api_webhook

    cleaned = validate_webhook_url(url)
    wanted = [e for e in (events or list(DEFAULT_EVENTS)) if e in ALLOWED_EVENTS]
    if not wanted:
        raise ValueError("webhook_events_invalid")
    public_id = f"wh_{secrets.token_hex(8)}"
    row = await insert_decision_api_webhook(
        public_id=public_id,
        org_id=str(principal["org_id"]),
        key_public_id=str(principal["public_id"]),
        url=cleaned,
        events=wanted,
        created_at=_utcnow(),
    )
    row["events"] = wanted
    row["enabled"] = True
    return public_webhook_view(row)


async def deliver_webhook_event(
    *,
    principal: dict[str, Any],
    event_type: str,
    payload: dict[str, Any],
    webhook_id: str | None = None,
) -> list[dict[str, Any]]:
    from database import (
        fetch_decision_api_webhook,
        insert_decision_api_webhook_delivery,
        list_decision_api_webhooks,
        touch_decision_api_webhook_delivery,
    )
    from secrets_vault import decrypt_secret

    if event_type not in ALLOWED_EVENTS:
        raise ValueError("webhook_events_invalid")
    org_id = str(principal.get("org_id") or "")
    if webhook_id:
        row = await fetch_decision_api_webhook(webhook_id, org_id=org_id)
        hooks = [row] if row and row.get("enabled") else []
    else:
        hooks = [h for h in await list_decision_api_webhooks(org_id=org_id) if h.get("enabled")]
    results: list[dict[str, Any]] = []
    signing = ""
    try:
        signing = decrypt_secret(str(principal.get("signing_secret_encrypted") or ""))
    except Exception:
        signing = ""
    for hook in hooks:
        events = hook.get("events") or []
        if event_type != "ping" and event_type not in events:
            continue
        delivery_id = f"del_{secrets.token_hex(8)}"
        timestamp = str(int(time.time()))
        body_obj = {
            "api_version": "v1",
            "event": event_type,
            "delivery_id": delivery_id,
            "org_id": org_id,
            "created_at": _utcnow(),
            "data": payload,
        }
        body = json.dumps(body_obj, sort_keys=True, separators=(",", ":"), default=str)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "blackdark-decision-api/1.1",
            "X-Blackdark-Event": event_type,
            "X-Blackdark-Timestamp": timestamp,
            "X-Blackdark-Delivery": delivery_id,
            "X-Blackdark-Signature": sign_webhook_body(signing or "unsigned", timestamp, body),
        }
        status: int | None = None
        error: str | None = None
        try:
            validate_webhook_url(str(hook.get("url") or ""))
            status = await _post_webhook(str(hook["url"]), body.encode("utf-8"), headers)
        except Exception as exc:
            error = str(exc)[:180]
            logger.info("Decision API webhook delivery failed | event=%s", event_type)
        await touch_decision_api_webhook_delivery(
            str(hook["public_id"]),
            status=status,
            error=error,
            delivered_at=_utcnow(),
        )
        await insert_decision_api_webhook_delivery(
            webhook_id=str(hook["public_id"]),
            org_id=org_id,
            event_type=event_type,
            delivery_id=delivery_id,
            status=status,
            error=error,
        )
        results.append(
            {
                "webhook_id": hook.get("public_id"),
                "delivery_id": delivery_id,
                "status": status,
                "ok": bool(status and 200 <= int(status) < 300),
                "error": error,
            }
        )
    return results


def schedule_webhook_delivery(
    principal: dict[str, Any],
    event_type: str,
    payload: dict[str, Any],
) -> None:
    """Fire-and-forget signed delivery. Empty hook list performs no HTTP."""
    import asyncio

    async def _run() -> None:
        try:
            await deliver_webhook_event(principal=principal, event_type=event_type, payload=payload)
        except Exception:
            logger.debug("Decision API webhook schedule failed", exc_info=True)

    try:
        asyncio.get_running_loop().create_task(_run())
    except RuntimeError:
        return


async def _post_webhook(url: str, body: bytes, headers: dict[str, str]) -> int:
    import aiohttp

    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, data=body, headers=headers, allow_redirects=False) as resp:
            return int(resp.status)
