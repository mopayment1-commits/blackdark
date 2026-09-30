"""Webhook verify → claim → process lifecycle with retry/DLQ (FDS-19 / SDG-11)."""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Awaitable, Callable

from transport_webhook_env.access_audit import record_production_access_event

_CLAIM_LOCK = threading.Lock()
_INFLIGHT: set[str] = set()

_MAX_RETRIES = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))
_RETRY_BASE_SEC = int(os.getenv("WEBHOOK_RETRY_BASE_SEC", "30"))
_REPLAY_TOLERANCE_SEC = int(os.getenv("WEBHOOK_REPLAY_TOLERANCE_SEC", "300"))


def _ledger_path() -> str:
    from pathlib import Path

    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return str(root / "webhook_lifecycle_evidence.jsonl")


def _append_event(event: dict[str, Any]) -> None:
    with open(_ledger_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def _sanitize_reason(reason: str) -> str:
    cleaned = (reason or "").strip().replace("\n", " ")
    for token in ("sk_live", "sk_test", "whsec_", "api_key", "secret"):
        if token in cleaned.lower():
            return "security_validation_failed"
    return cleaned[:240]


def check_replay_window(provider: str, event: dict[str, Any]) -> bool:
    now = time.time()
    if provider == "stripe":
        created = event.get("created")
        if created is None:
            return True
        try:
            age = now - float(created)
        except (TypeError, ValueError):
            return False
        return age <= _REPLAY_TOLERANCE_SEC
    if provider == "lemon_squeezy":
        meta = event.get("meta") or {}
        test_mode = bool(meta.get("test_mode"))
        if test_mode and environment_identity() == "production":
            return False
        ts = meta.get("created_at") or meta.get("updated_at")
        if not ts:
            return True
        try:
            from datetime import datetime

            if isinstance(ts, (int, float)):
                age = now - float(ts)
            else:
                parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                age = now - parsed.timestamp()
        except Exception:
            return False
        return age <= _REPLAY_TOLERANCE_SEC
    return True


def environment_identity() -> str:
    from transport_webhook_env.environment import environment_identity as _env

    return _env()


async def _atomic_claim(provider: str, event_id: str, event_type: str) -> bool:
    key = f"{provider}:{event_id}"
    with _CLAIM_LOCK:
        if key in _INFLIGHT:
            return False
        _INFLIGHT.add(key)
    try:
        from database import claim_billing_webhook_event

        return await claim_billing_webhook_event(provider=provider, event_id=event_id, event_type=event_type)
    finally:
        with _CLAIM_LOCK:
            _INFLIGHT.discard(key)


def schedule_retry(
    *,
    provider: str,
    event_id: str,
    reason: str,
    retry_count: int,
    correlation_id: str,
) -> dict[str, Any]:
    if retry_count >= _MAX_RETRIES:
        return move_to_dead_letter(
            provider=provider,
            event_id=event_id,
            reason=reason,
            retry_count=retry_count,
            correlation_id=correlation_id,
        )
    next_retry = time.time() + _RETRY_BASE_SEC * (2 ** max(0, retry_count - 1))
    rec = {
        "state": "RETRY_SCHEDULED",
        "provider": provider,
        "event_id": event_id,
        "reason": _sanitize_reason(reason),
        "retry_count": retry_count,
        "next_retry_at": next_retry,
        "correlation_id": correlation_id,
        "ts": time.time(),
    }
    _append_event(rec)
    return rec


def move_to_dead_letter(
    *,
    provider: str,
    event_id: str,
    reason: str,
    retry_count: int,
    correlation_id: str,
) -> dict[str, Any]:
    rec = {
        "state": "DEAD_LETTER",
        "provider": provider,
        "event_id": event_id,
        "reason": _sanitize_reason(reason),
        "retry_count": retry_count,
        "final_disposition": "dead_letter",
        "correlation_id": correlation_id,
        "ts": time.time(),
    }
    _append_event(rec)
    record_production_access_event(
        actor="webhook_processor",
        action="webhook.dead_letter",
        target=f"{provider}:{event_id}",
        outcome="dead_letter",
        correlation_id=correlation_id,
        detail={"reason": rec["reason"], "retry_count": retry_count},
    )
    return rec


def reject_security_event(
    *,
    provider: str,
    reason: str,
    correlation_id: str,
) -> dict[str, Any]:
    rec = {
        "state": "REJECTED_SECURITY",
        "provider": provider,
        "reason": _sanitize_reason(reason),
        "correlation_id": correlation_id,
        "ts": time.time(),
    }
    _append_event(rec)
    record_production_access_event(
        actor="webhook_gateway",
        action="webhook.security_reject",
        target=provider,
        outcome="rejected",
        correlation_id=correlation_id,
        detail={"reason": rec["reason"]},
    )
    return rec


async def process_verified_webhook(
    *,
    provider: str,
    event_id: str,
    event_type: str,
    event: dict[str, Any],
    processor: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    correlation_id: str,
    retry_count: int = 0,
) -> dict[str, Any]:
    if not check_replay_window(provider, event):
        return reject_security_event(provider=provider, reason="replay_window_violation", correlation_id=correlation_id)

    claimed = await _atomic_claim(provider, event_id, event_type)
    if not claimed:
        rec = {
            "state": "SUCCESS",
            "provider": provider,
            "event_id": event_id,
            "action": "duplicate_ignored",
            "correlation_id": correlation_id,
            "ts": time.time(),
        }
        _append_event(rec)
        return {"received": True, "handled": True, "action": "duplicate_ignored", "event_id": event_id}

    _append_event(
        {
            "state": "CLAIM",
            "provider": provider,
            "event_id": event_id,
            "event_type": event_type,
            "correlation_id": correlation_id,
            "ts": time.time(),
        }
    )
    try:
        result = await processor(event)
        if result.get("handled"):
            _append_event(
                {
                    "state": "SUCCESS",
                    "provider": provider,
                    "event_id": event_id,
                    "action": result.get("action"),
                    "correlation_id": correlation_id,
                    "ts": time.time(),
                }
            )
            record_production_access_event(
                actor="webhook_processor",
                action="webhook.processed",
                target=f"{provider}:{event_id}",
                outcome="success",
                correlation_id=correlation_id,
                detail={"action": result.get("action")},
            )
            return {"received": True, **result}
        retry = schedule_retry(
            provider=provider,
            event_id=event_id,
            reason=str(result.get("reason") or "unhandled"),
            retry_count=retry_count + 1,
            correlation_id=correlation_id,
        )
        return {"received": True, "handled": False, "lifecycle": retry}
    except Exception as exc:
        if isinstance(exc, (PermissionError, ValueError)) and "security" in str(exc).lower():
            return reject_security_event(provider=provider, reason=str(exc), correlation_id=correlation_id)
        retry = schedule_retry(
            provider=provider,
            event_id=event_id,
            reason=str(exc),
            retry_count=retry_count + 1,
            correlation_id=correlation_id,
        )
        return {"received": True, "handled": False, "lifecycle": retry}
