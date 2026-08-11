"""
BLACKDARK — Durable email outbox (works without SMTP; flushes when configured).

When SMTP_HOST is unset, alerts are queued to data/email_outbox.jsonl.
When SMTP is later configured, flush_email_outbox() sends pending rows.

Message bodies are Fernet-sealed at rest so password-reset copy never lands
as clear text on disk (CodeQL clear-text storage).
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_PATH = Path("data/email_outbox.jsonl")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


_SENSITIVE_KEYS = ("password", "passwd", "secret", "api_key", "authorization", "private_key")


def _seal_body(body: str) -> str:
    from secrets_vault import encrypt_secret

    return encrypt_secret(body or "")


def _unseal_body(row: dict[str, Any]) -> str:
    sealed = row.get("body_sealed")
    if sealed:
        from secrets_vault import decrypt_secret

        try:
            return decrypt_secret(str(sealed))
        except Exception:
            return ""
    # Legacy rows written before sealing (best-effort read).
    return str(row.get("body") or "")


def _redact_for_disk(row: dict[str, Any]) -> dict[str, Any]:
    """Persist outbox without clear-text body or secret payload fields."""
    out = dict(row)
    payload = out.get("payload") or {}
    if isinstance(payload, dict):
        out["payload"] = {
            k: ("[redacted]" if any(s in str(k).lower() for s in _SENSITIVE_KEYS) else v)
            for k, v in payload.items()
        }
    body = str(out.pop("body", "") or "")
    out["body_sealed"] = _seal_body(body)
    out["body"] = ""
    return out


def enqueue_email(
    to_email: str,
    subject: str,
    body: str,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "id": f"eml_{uuid4().hex[:12]}",
        "to": to_email,
        "subject": subject,
        "body": body,
        "payload": payload or {},
        "status": "queued",
        "created_at": _utcnow(),
        "sent_at": None,
        "error": None,
    }
    with _LOCK:
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        with _PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(_redact_for_disk(row), separators=(",", ":"), default=str) + "\n")
    # Return in-memory row (includes clear body) for immediate senders.
    return dict(row)


def list_queued(*, limit: int = 50) -> list[dict[str, Any]]:
    if not _PATH.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with _LOCK:
        for line in _PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("json parse skipped", exc_info=True)
                continue
            if row.get("status") == "queued":
                row = dict(row)
                row["body"] = _unseal_body(row)
                rows.append(row)
    return rows[-max(1, min(limit, 200)) :]


async def flush_email_outbox(*, limit: int = 50) -> dict[str, Any]:
    """Send queued emails if SMTP_HOST is configured."""
    if not os.getenv("SMTP_HOST", "").strip():
        return {
            "flushed": 0,
            "pending": len(list_queued(limit=200)),
            "status": "smtp_not_configured",
        }
    from alert_service import send_email_alert

    queued = list_queued(limit=limit)
    sent = 0
    failed = 0
    kept: list[dict[str, Any]] = []
    if _PATH.is_file():
        with _LOCK:
            all_rows: list[dict[str, Any]] = []
            for line in _PATH.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    all_rows.append(json.loads(line))
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.debug("json parse skipped", exc_info=True)
                    continue
            id_set = {r["id"] for r in queued}
            for row in all_rows:
                if row.get("id") in id_set and row.get("status") == "queued":
                    body = _unseal_body(row)
                    ok = await send_email_alert(row["to"], row["subject"], body)
                    if ok:
                        row["status"] = "sent"
                        row["sent_at"] = _utcnow()
                        row["body"] = ""
                        sent += 1
                    else:
                        row["status"] = "failed"
                        row["error"] = "smtp_send_failed"
                        failed += 1
                # Never rewrite clear-text bodies onto disk.
                if row.get("body"):
                    row["body"] = ""
                kept.append(row)

            def _write() -> None:
                with _PATH.open("w", encoding="utf-8") as fh:
                    for item in kept:
                        fh.write(json.dumps(item, separators=(",", ":"), default=str) + "\n")

            await asyncio.to_thread(_write)
    return {"flushed": sent, "failed": failed, "pending": len(list_queued(limit=200))}
