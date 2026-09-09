"""Webhook security helpers — signature, replay, audit."""

from __future__ import annotations

import hashlib
import time
from typing import Any


async def record_webhook_signature_failure(*, provider: str, reason: str) -> None:
    try:
        from security_events import record_security_event

        record_security_event(
            event_type="webhook_signature_failure",
            severity="high",
            detail={"provider": provider, "reason": reason},
        )
    except Exception:
        pass
    try:
        from billing.observability import record_webhook_signature_failure_metric

        await record_webhook_signature_failure_metric(provider=provider, reason=reason)
    except Exception:
        pass


def webhook_replay_key(*, provider: str, event_id: str, payload_hash: str) -> str:
    return hashlib.sha256(f"{provider}:{event_id}:{payload_hash}".encode()).hexdigest()


def validate_webhook_timestamp(*, timestamp: int | None, tolerance_seconds: int = 300) -> bool:
    if timestamp is None:
        return True
    return abs(int(time.time()) - int(timestamp)) <= tolerance_seconds


def webhook_security_status() -> dict[str, Any]:
    return {
        "stripe_signature": "stripe.Webhook.construct_event",
        "lemon_hmac": "billing_service.verify_lemon_webhook_signature",
        "idempotency": "database.claim_billing_webhook_event",
        "replay_protection": True,
        "timestamp_tolerance_seconds": 300,
    }
