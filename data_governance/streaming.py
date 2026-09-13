"""Streaming ingestion governance (DIG-002, DIG-010–012, DIG-033)."""

from __future__ import annotations

from typing import Any


def validate_stream_event(event: dict[str, Any]) -> dict[str, Any]:
    required = ("source_id", "event_type", "observed_at")
    missing = [k for k in required if not event.get(k)]
    ok = not missing
    return {"ok": ok, "missing": missing, "transport": "websocket_first"}


def assert_stream_admission(event: dict[str, Any]) -> None:
    result = validate_stream_event(event)
    if not result["ok"]:
        from blackdark.data_governance.runtime import GovernanceViolationError

        raise GovernanceViolationError(f"stream_admission_denied:{','.join(result['missing'])}")
