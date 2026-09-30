"""Failure observability SLI hooks (ERR-023)."""

from __future__ import annotations

from typing import Any


def increment_failure_metric(name: str) -> None:
    try:
        from observability import increment_metric

        increment_metric(name)
    except Exception:
        pass


def record_failure_sli(
    *,
    failure_class: str,
    retry_count: int = 0,
    fallback_used: bool = False,
    stale: bool = False,
    partial: bool = False,
    indeterminate: bool = False,
) -> None:
    increment_failure_metric("failure_events_total")
    increment_failure_metric(f"failure_class_{failure_class.lower()}_total")
    if retry_count:
        increment_failure_metric("failure_retry_total")
    if fallback_used:
        increment_failure_metric("failure_fallback_total")
    if stale:
        increment_failure_metric("failure_stale_total")
    if partial:
        increment_failure_metric("failure_partial_total")
    if indeterminate:
        increment_failure_metric("failure_indeterminate_total")


def snapshot_metrics() -> dict[str, Any]:
    try:
        from observability import observability_status

        return observability_status()
    except Exception:
        return {}
