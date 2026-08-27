"""Explicit dataset state metadata (BLACKDARK_CONTEXT D-01)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# LIVE: rows returned | MISSING: no rows | STALE: exceeds SLA | UNKNOWN: upstream/circuit open
DATA_STATE_LIVE = "LIVE"
DATA_STATE_MISSING = "MISSING"
DATA_STATE_STALE = "STALE"
DATA_STATE_UNKNOWN = "UNKNOWN"

DEFAULT_SLA_SECONDS = {
    "ohlcv": 7200,
    "funding_rates": 28800,
    "open_interest": 7200,
    "events": 86400,
}


def _parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def resolve_data_state(
    *,
    count: int,
    dataset: str,
    latest_record_at: str | None = None,
    freshness_sla_seconds: int | None = None,
    upstream_unknown: bool = False,
) -> tuple[str, str | None]:
    if upstream_unknown:
        return DATA_STATE_UNKNOWN, "upstream_circuit_open_or_ingest_failed"
    if count <= 0:
        return DATA_STATE_MISSING, f"no_{dataset}_records_for_query"
    sla = freshness_sla_seconds or DEFAULT_SLA_SECONDS.get(dataset, 3600)
    if latest_record_at:
        parsed = _parse_iso(latest_record_at)
        if parsed:
            age = (datetime.now(UTC) - parsed).total_seconds()
            if age > sla:
                return DATA_STATE_STALE, f"latest_record_age_{int(age)}s_exceeds_sla_{sla}s"
    return DATA_STATE_LIVE, None


def dataset_response(
    *,
    count: int,
    data: list[Any],
    dataset: str,
    symbol: str | None = None,
    interval: str | None = None,
    latest_record_at: str | None = None,
    freshness_sla_seconds: int | None = None,
    upstream_unknown: bool = False,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read API payload with explicit data_state (empty ≠ zero)."""
    data_state, reason = resolve_data_state(
        count=count,
        dataset=dataset,
        latest_record_at=latest_record_at,
        freshness_sla_seconds=freshness_sla_seconds,
        upstream_unknown=upstream_unknown,
    )

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
    sla = freshness_sla_seconds or DEFAULT_SLA_SECONDS.get(dataset)
    if sla is not None:
        body["freshness_sla_seconds"] = sla
    if extra:
        body.update(extra)
    return body
