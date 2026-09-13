"""UTC timestamp formatting — canonical clock authority for data governance."""

from __future__ import annotations

from datetime import UTC, datetime

from data_governance.timestamps import build_timestamps


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def format_observed_at(epoch_seconds: float | None = None) -> str:
    ts = epoch_seconds if epoch_seconds is not None else datetime.now(UTC).timestamp()
    return datetime.fromtimestamp(ts, tz=UTC).isoformat()


def timestamp_bundle(**kwargs):
    return build_timestamps(**kwargs)
