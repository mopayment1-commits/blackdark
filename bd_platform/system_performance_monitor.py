"""
System Performance Monitor — Feature #414 (Sprint-0 Infrastructure).

Renamed from Execution_Latency_Monitor — internal observability only.
Distributed tracing, p50/p95/p99, stage attribution, SLO breach detection.
NOT a user-facing product feature.
"""

from __future__ import annotations

import json
import logging
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.SystemPerformanceMonitor")

_FEATURE_ID = 414
_TITLE = "System Performance Monitor"
_RENAMED_FROM = "Execution_Latency_Monitor"
_STANDALONE = False
_MERGED_INTO = "Sprint-0 Infrastructure / Observability Layer"
_PRIORITY = "low"
_INTERNAL_ADMIN_ONLY = True
_SEED_PATH = Path("data/system_performance_monitor_seed.json")
_METHODOLOGY_VERSION = "1.0"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"spans": {}, "slo_targets_ms": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("system performance monitor seed load failed: %s", exc)
        return {"spans": {}, "slo_targets_ms": {}}


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return round(values[0], 3)
    sorted_vals = sorted(values)
    idx = min(len(sorted_vals) - 1, max(0, int(p / 100 * len(sorted_vals))))
    return round(sorted_vals[idx], 3)


def compute_trace_latency(spans: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate spans by trace_id — no averaged-away tail latency (report p99 separately)."""
    by_trace: dict[str, list[dict[str, Any]]] = {}
    for span in spans:
        tid = span.get("trace_id", "unknown")
        by_trace.setdefault(tid, []).append(span)

    traces = []
    total_durations: list[float] = []
    for trace_id, trace_spans in by_trace.items():
        total_ms = sum(float(s.get("duration_ms", 0)) for s in trace_spans)
        total_durations.append(total_ms)
        traces.append({
            "trace_id": trace_id,
            "total_duration_ms": round(total_ms, 3),
            "stages": [
                {"stage": s.get("stage"), "duration_ms": s.get("duration_ms")}
                for s in trace_spans
            ],
        })

    return {
        "trace_count": len(traces),
        "traces": traces,
        "p50_ms": _percentile(total_durations, 50),
        "p95_ms": _percentile(total_durations, 95),
        "p99_ms": _percentile(total_durations, 99),
        "max_ms": round(max(total_durations), 3) if total_durations else 0,
        "mean_ms": round(statistics.mean(total_durations), 3) if total_durations else 0,
        "no_averaged_away_tail_latency": True,
        "tail_reported_via_p99": True,
    }


def build_stage_attribution(system: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    spans = (seed.get("spans") or {}).get(system, [])
    by_stage: dict[str, list[float]] = {}
    for span in spans:
        stage = span.get("stage", "unknown")
        by_stage.setdefault(stage, []).append(float(span.get("duration_ms", 0)))

    stages = {
        stage: {
            "count": len(durations),
            "p50_ms": _percentile(durations, 50),
            "p95_ms": _percentile(durations, 95),
            "p99_ms": _percentile(durations, 99),
        }
        for stage, durations in by_stage.items()
    }

    bottleneck = max(stages.items(), key=lambda x: x[1]["p95_ms"], default=(None, {}))

    return {
        "system": system,
        "stage_attribution": stages,
        "bottleneck_stage": bottleneck[0],
        "bottleneck_p95_ms": bottleneck[1].get("p95_ms") if bottleneck[1] else None,
        "display": f"{system} bottleneck: {bottleneck[0]} (p95={bottleneck[1].get('p95_ms', 'N/A')}ms)",
    }


def detect_slo_breaches(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    targets = seed.get("slo_targets_ms") or {}
    breaches: list[dict[str, Any]] = []

    for system in seed.get("systems") or []:
        spans = (seed.get("spans") or {}).get(system, [])
        latency = compute_trace_latency(spans)
        target_key = f"{system}_p95"
        target = float(targets.get(target_key, 9999))
        p95 = latency.get("p95_ms", 0)

        if p95 > target:
            breaches.append({
                "system": system,
                "metric": "p95",
                "value_ms": p95,
                "target_ms": target,
                "severity": "elevated",
                "display": f"SLO breach: {system} p95={p95}ms > target {target}ms",
            })

    return {
        "slo_breaches": breaches,
        "breach_count": len(breaches),
        "clock_sync_required": seed.get("clock_sync_required", True),
        "trace_ids_required": seed.get("trace_ids_required", True),
    }


def build_performance_panel() -> dict[str, Any]:
    seed = _load_seed()
    systems_report = {}
    for system in seed.get("systems") or []:
        spans = (seed.get("spans") or {}).get(system, [])
        systems_report[system] = {
            "latency": compute_trace_latency(spans),
            "stage_attribution": build_stage_attribution(system, seed),
        }

    slo = detect_slo_breaches(seed)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "internal_admin_only": _INTERNAL_ADMIN_ONLY,
        "not_user_facing": True,
        "systems": systems_report,
        "slo": slo,
        "load_evidence": seed.get("load_evidence") or {},
        "principles": {
            "clock_sync": seed.get("clock_sync_required", True),
            "trace_ids": seed.get("trace_ids_required", True),
            "no_averaged_away_tail_latency": seed.get("no_averaged_away_tail_latency", True),
        },
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def system_performance_monitor_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "internal_admin_only": _INTERNAL_ADMIN_ONLY,
        "not_user_facing": True,
        "systems_monitored": seed.get("systems") or [],
        "admin_endpoint": "/api/platform/internal/system-performance",
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_product_feature", "passed": seed.get("internal_admin_only") is True, "detail": "admin only"})
    checks.append({"id": "renamed_from_execution", "passed": seed.get("renamed_from") == "Execution_Latency_Monitor", "detail": "renamed"})
    checks.append({"id": "trace_ids", "passed": seed.get("trace_ids_required") is True, "detail": "trace IDs"})
    checks.append({"id": "clock_sync", "passed": seed.get("clock_sync_required") is True, "detail": "clock sync"})

    panel = build_performance_panel()
    checks.append({"id": "p50_p95_p99", "passed": "p99_ms" in panel["systems"]["oracle_api"]["latency"], "detail": "percentiles"})
    checks.append({"id": "stage_attribution", "passed": panel["systems"]["oracle_api"]["stage_attribution"].get("bottleneck_stage") is not None, "detail": "bottleneck"})
    checks.append({"id": "load_evidence", "passed": panel.get("load_evidence", {}).get("passed") is True, "detail": "load test"})
    checks.append({"id": "no_averaged_tail", "passed": seed.get("no_averaged_away_tail_latency") is True, "detail": "p99 separate"})

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
