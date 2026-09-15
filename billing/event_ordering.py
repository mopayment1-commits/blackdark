"""Billing webhook event ordering — prevent stale provider snapshots rewinding state."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def should_apply_provider_subscription_event(
    stored: dict[str, Any] | None,
    *,
    period_end: str | None,
    event_created_at: int | float | None,
) -> tuple[bool, str]:
    """Return (apply, reason). Reject older provider snapshots without mutating state."""
    if not stored:
        return True, "no_existing_subscription"
    stored_created = stored.get("last_provider_event_created")
    if event_created_at is not None and stored_created is not None:
        try:
            if float(event_created_at) < float(stored_created):
                return False, "out_of_order_provider_event_created"
        except (TypeError, ValueError):
            pass
    stored_end = _parse_iso(stored.get("current_period_end"))
    incoming_end = _parse_iso(period_end)
    if stored_end and incoming_end and incoming_end < stored_end:
        return False, "out_of_order_period_end"
    return True, "accepted"
