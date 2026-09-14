"""Temporal spine operational metrics (Prometheus counters via observability.py)."""

from __future__ import annotations

from typing import Any

_METRIC_NAMES = frozenset(
    {
        "temporal_spine_runs_total",
        "temporal_spine_ingest_success_total",
        "temporal_spine_ingest_rejected_total",
        "temporal_pit_violations_total",
        "temporal_leakage_violations_total",
        "temporal_contamination_violations_total",
        "temporal_db_failures_total",
        "temporal_replay_failures_total",
        "temporal_evidence_persistence_failures_total",
        "temporal_reality_anchor_pending_total",
        "temporal_reality_anchor_verified_total",
        "temporal_api_requests_total",
        "temporal_api_errors_total",
        "temporal_live_feed_ingest_total",
        "temporal_spine_latency_ms_total",
    }
)


def increment_temporal_metric(name: str, amount: float = 1.0) -> None:
    if name not in _METRIC_NAMES:
        raise ValueError(f"unknown temporal metric: {name}")
    from observability import increment_metric

    increment_metric(name, amount)


def record_spine_latency_ms(latency_ms: float) -> None:
    increment_temporal_metric("temporal_spine_latency_ms_total", latency_ms)


def record_spine_outcome(
    *,
    status: str,
    error_code: str | None = None,
    reality_anchor_pending: bool = False,
    latency_ms: float | None = None,
) -> None:
    increment_temporal_metric("temporal_spine_runs_total")
    if status == "completed":
        increment_temporal_metric("temporal_spine_ingest_success_total")
        if reality_anchor_pending:
            increment_temporal_metric("temporal_reality_anchor_pending_total")
        else:
            increment_temporal_metric("temporal_reality_anchor_verified_total")
    else:
        increment_temporal_metric("temporal_spine_ingest_rejected_total")
        if error_code == "PIT_RECONSTRUCTION_EMPTY" or (error_code and error_code.startswith("PIT")):
            increment_temporal_metric("temporal_pit_violations_total")
        elif error_code == "TEMPORAL_LEAKAGE_REJECTED":
            increment_temporal_metric("temporal_leakage_violations_total")
        elif error_code == "INGESTION_PIT_CONTRACT_INCOMPLETE":
            increment_temporal_metric("temporal_pit_violations_total")
    if latency_ms is not None:
        record_spine_latency_ms(latency_ms)


def record_contamination_rejection() -> None:
    increment_temporal_metric("temporal_contamination_violations_total")
    increment_temporal_metric("temporal_spine_ingest_rejected_total")


def temporal_metrics_status() -> dict[str, Any]:
    from observability import observability_status

    counters = observability_status().get("counters", {})
    return {name: counters.get(name, 0.0) for name in sorted(_METRIC_NAMES)}
