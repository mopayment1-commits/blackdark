"""
Data Engine Quality Monitor — Feature #824 (Sprint-0 infrastructure).

NOT standalone — merged into Data Engine as quality_monitor.
Feeds #789 Infrastructure Observability. Overlaps #850 Data Quality Pipeline.

No user-facing surface — internal Grafana dashboard only.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DataEngineQualityMonitor")

_FEATURE_REF = 824
_STANDALONE = False
_MERGED_INTO = "Data Engine"
_COMPONENT = "quality_monitor"
_INFRA_OBS_REF = 789
_DATA_QUALITY_PIPELINE_REF = 850
_SEED_PATH = Path("data/data_engine_quality_monitor_seed.json")
_DAILY_CHECKS = ("gap_detection", "outlier_detection", "reconciliation")
_ACCURACY_TARGET_PCT = 99.99
_QUERY_LATENCY_TARGET_MS = 1000
_RETENTION_YEARS_MIN = 2

CheckType = Literal["gap_detection", "outlier_detection", "reconciliation"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("quality monitor seed load failed: %s", exc)
        return {}


def _run_gap_detection(dataset: dict[str, Any]) -> dict[str, Any]:
    timestamps = dataset.get("timestamps") or []
    gaps = []
    for i in range(1, len(timestamps)):
        delta = timestamps[i] - timestamps[i - 1]
        expected = dataset.get("expected_interval_sec", 3600)
        if delta > expected * 1.5:
            gaps.append({"index": i, "gap_sec": delta, "expected_sec": expected})
    return {
        "check": "gap_detection",
        "passed": len(gaps) == 0,
        "gaps_found": len(gaps),
        "gaps": gaps[:5],
        "records_checked": len(timestamps),
    }


def _run_outlier_detection(dataset: dict[str, Any]) -> dict[str, Any]:
    values = [float(v) for v in (dataset.get("values") or [])]
    if len(values) < 5:
        return {"check": "outlier_detection", "passed": True, "outliers_found": 0, "records_checked": len(values)}
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5
    threshold = float(dataset.get("outlier_std_threshold", 3.0))
    outliers = [
        {"index": i, "value": v, "z_score": round(abs(v - mean) / std, 2) if std else 0}
        for i, v in enumerate(values)
        if std and abs(v - mean) / std > threshold
    ]
    return {
        "check": "outlier_detection",
        "passed": len(outliers) <= int(dataset.get("max_outliers_allowed", 2)),
        "outliers_found": len(outliers),
        "outliers": outliers[:5],
        "records_checked": len(values),
    }


def _run_reconciliation(dataset: dict[str, Any]) -> dict[str, Any]:
    source_a = float(dataset.get("source_a_total", 0))
    source_b = float(dataset.get("source_b_total", 0))
    tolerance_pct = float(dataset.get("tolerance_pct", 0.01))
    if source_a == 0:
        delta_pct = 0.0
    else:
        delta_pct = abs(source_a - source_b) / source_a * 100
    return {
        "check": "reconciliation",
        "passed": delta_pct <= tolerance_pct,
        "source_a_total": source_a,
        "source_b_total": source_b,
        "delta_pct": round(delta_pct, 4),
        "tolerance_pct": tolerance_pct,
    }


_CHECK_RUNNERS = {
    "gap_detection": _run_gap_detection,
    "outlier_detection": _run_outlier_detection,
    "reconciliation": _run_reconciliation,
}


def run_daily_quality_check_824(
    check_type: CheckType,
    dataset_id: str = "market_ohlcv",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one of 3 daily data quality checks."""
    seed = seed or _load_seed()
    if check_type not in _DAILY_CHECKS:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "invalid_check_type", "check_type": check_type}

    datasets = (seed.get("datasets") or {})
    dataset = datasets.get(dataset_id) or {}
    t0 = time.perf_counter()
    result = _CHECK_RUNNERS[check_type](dataset)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "ok": result.get("passed", False),
        "feature_ref": _FEATURE_REF,
        "component": _COMPONENT,
        "check_type": check_type,
        "dataset_id": dataset_id,
        "schedule": "daily",
        "result": result,
        "query_latency_ms": latency_ms,
        "within_query_target": latency_ms <= _QUERY_LATENCY_TARGET_MS,
        "timestamp": _utcnow(),
    }


def run_all_daily_quality_checks_824(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run all 3 daily checks: gap | outlier | reconciliation."""
    seed = seed or _load_seed()
    checks = []
    for check_type in _DAILY_CHECKS:
        checks.append(run_daily_quality_check_824(check_type, seed=seed))

    all_passed = all(c.get("ok") for c in checks)
    metrics = seed.get("current_metrics") or {}
    accuracy = float(metrics.get("accuracy_pct", 0))

    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "component": _COMPONENT,
        "daily_checks": list(_DAILY_CHECKS),
        "checks_run": len(checks),
        "checks": checks,
        "accuracy_pct": accuracy,
        "accuracy_target_pct": _ACCURACY_TARGET_PCT,
        "within_accuracy_target": accuracy >= _ACCURACY_TARGET_PCT,
        "accuracy_internal_only": True,
        "no_user_promise": True,
        "timestamp": _utcnow(),
    }


def build_quality_monitor_panel_824(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Internal quality monitor panel — feeds Grafana via #789."""
    seed = seed or _load_seed()
    cfg = seed.get("quality_monitor_824") or {}
    checks = run_all_daily_quality_checks_824(seed=seed)
    metrics = seed.get("current_metrics") or {}
    retention = cfg.get("retention_policy") or {}

    return {
        "ok": checks.get("ok", False),
        "feature_ref": _FEATURE_REF,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "standalone_rejected": True,
        "no_user_surface": True,
        "internal_dashboard": "Grafana (team only)",
        "infra_observability_ref": _INFRA_OBS_REF,
        "data_quality_pipeline_ref": _DATA_QUALITY_PIPELINE_REF,
        "pipeline_stages": [
            "1_collect",
            "2_clean_normalize",
            "3_store",
            "4_query",
            "5_display_internal_only",
        ],
        "data_domains": ["market", "onchain", "user"],
        "daily_checks": checks,
        "internal_targets": {
            "accuracy_pct": _ACCURACY_TARGET_PCT,
            "accuracy_internal_only": True,
            "query_latency_ms": _QUERY_LATENCY_TARGET_MS,
            "query_latency_internal_only": True,
            "current_accuracy_pct": metrics.get("accuracy_pct"),
            "current_query_latency_p99_ms": metrics.get("query_latency_p99_ms"),
            "within_accuracy_target": float(metrics.get("accuracy_pct", 0)) >= _ACCURACY_TARGET_PCT,
            "within_query_target": float(metrics.get("query_latency_p99_ms", 9999)) <= _QUERY_LATENCY_TARGET_MS,
        },
        "retention_policy": {
            "min_years": _RETENTION_YEARS_MIN,
            "configured_years": retention.get("years", _RETENTION_YEARS_MIN),
            "infrastructure_concern": True,
            "cold_storage_enabled": retention.get("cold_storage_enabled", True),
        },
        "export_deferred": True,
        "user_reports_deferred": True,
        "fee_db": cfg.get("fee_db") or seed.get("fee_db") or {
            "monitoring_usd": 25.0,
            "storage_usd": 15.0,
            "tier": "ops",
            "ops_budget": True,
        },
        "timestamp": _utcnow(),
    }


def build_infra_observability_quality_feed_824(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#824 → #789 Infrastructure Observability feed."""
    panel = build_quality_monitor_panel_824(seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": _FEATURE_REF,
        "feeds": f"#{_INFRA_OBS_REF} Infrastructure Observability",
        "quality_metrics": {
            "accuracy_pct": panel.get("internal_targets", {}).get("current_accuracy_pct"),
            "query_latency_p99_ms": panel.get("internal_targets", {}).get("current_query_latency_p99_ms"),
            "daily_checks_passed": (panel.get("daily_checks") or {}).get("ok"),
            "retention_years": (panel.get("retention_policy") or {}).get("configured_years"),
        },
        "grafana_dashboard": "blackdark-data-quality-internal",
        "timestamp": _utcnow(),
    }


def run_quality_monitor_e2e_824(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """E2E: 3 daily checks + internal targets + #789 feed."""
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    status = quality_monitor_status_824(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": status.get("standalone_rejected") is True})
    tests.append({"test": "component_quality_monitor", "passed": status.get("component") == "quality_monitor"})
    tests.append({"test": "three_daily_checks", "passed": status.get("daily_checks") == list(_DAILY_CHECKS)})
    tests.append({"test": "no_user_surface", "passed": status.get("no_user_surface") is True})
    tests.append({"test": "accuracy_internal_only", "passed": status.get("accuracy_internal_only") is True})

    checks = run_all_daily_quality_checks_824(seed=seed)
    tests.append({"test": "all_daily_checks_run", "passed": checks.get("checks_run") == 3})
    tests.append({"test": "daily_checks_pass", "passed": checks.get("ok") is True})

    panel = build_quality_monitor_panel_824(seed=seed)
    tests.append({"test": "retention_2_years", "passed": (panel.get("retention_policy") or {}).get("configured_years", 0) >= 2})
    tests.append({"test": "query_latency_target", "passed": (panel.get("internal_targets") or {}).get("within_query_target") is True})

    feed = build_infra_observability_quality_feed_824(seed=seed)
    tests.append({"test": "feeds_infra_observability_789", "passed": feed.get("feeds") == "#789 Infrastructure Observability"})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }


def quality_monitor_status_824(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("quality_monitor_824") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "sprint": 0,
        "no_user_surface": True,
        "internal_dashboard": "Grafana (team only)",
        "infra_observability_ref": _INFRA_OBS_REF,
        "data_quality_pipeline_ref": _DATA_QUALITY_PIPELINE_REF,
        "daily_checks": list(_DAILY_CHECKS),
        "accuracy_target_pct": _ACCURACY_TARGET_PCT,
        "accuracy_internal_only": True,
        "no_user_promise": True,
        "query_latency_target_ms": _QUERY_LATENCY_TARGET_MS,
        "query_latency_internal_only": True,
        "retention_years_min": _RETENTION_YEARS_MIN,
        "data_domains": ["market", "onchain", "user"],
        "fee_db": cfg.get("fee_db") or seed.get("fee_db"),
        "timestamp": _utcnow(),
    }
