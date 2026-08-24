"""Explicit dataset state metadata (BLACKDARK_CONTEXT D-01)."""

from __future__ import annotations

from typing import Any

# LIVE: rows returned | MISSING: no rows for query | STALE: rows exist but exceed freshness SLA
DATA_STATE_LIVE = "LIVE"
DATA_STATE_MISSING = "MISSING"
DATA_STATE_STALE = "STALE"
DATA_STATE_UNKNOWN = "UNKNOWN"


def dataset_response(
    *,
    count: int,
    data: list[Any],
    dataset: str,
    symbol: str | None = None,
    interval: str | None = None,
    latest_record_at: str | None = None,
    freshness_sla_seconds: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read API payload with explicit data_state (empty ≠ zero)."""
    if count > 0:
        data_state = DATA_STATE_LIVE
        reason = None
    else:
        data_state = DATA_STATE_MISSING
        reason = f"no_{dataset}_records_for_query"

    body: dict[str, Any] = {
        "count": count,
        "data": data,
        "data_state": data_state,
    }
    if reason:
        body["data_state_reason"] = reason
    if symbol is not None:
        body["symbol"] = symbol.upper()
    if interval is not None:
        body["interval"] = interval
    if latest_record_at:
        body["latest_record_at"] = latest_record_at
    if freshness_sla_seconds is not None:
        body["freshness_sla_seconds"] = freshness_sla_seconds
    if extra:
        body.update(extra)
    return body
