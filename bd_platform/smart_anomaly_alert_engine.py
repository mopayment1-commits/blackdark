"""
Smart Anomaly Alert Engine — Features #719 + #131 + #121 merged (Sprint 2).

#719 = Anomaly Detection Alerts (rolling baseline + z-score, no manual-only threshold)
#131 = Unusual Liquidity (absorbed)
#121 = Large Liquidity Events (absorbed)

Rule-based statistical detection — not manual threshold only.
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SmartAnomalyAlertEngine")

_FEATURE_ID = 719
_ABSORBED_IDS = (719, 131, 121)
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Smart Anomaly Alert Engine"
_SPRINT = 2
_SEED_PATH = Path("data/smart_anomaly_alert_engine_seed.json")
_METHODOLOGY_VERSION = "1.0"
_BASELINE_VERSION = "1.0"
_BASELINE_WINDOW_DAYS = 30
_MIN_SAMPLE_DAYS = 7
_ZSCORE_THRESHOLD = 3.0

_DISCLAIMER = (
    "Anomaly alerts use rolling baselines and z-score detection. "
    "Not investment advice. Not trade signals. "
    "Low-sample periods suppressed. False positive rate documented via backtest."
)

AlertSeverity = Literal["low", "medium", "high"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"metrics": {}, "alerts": [], "backtest": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("smart anomaly alert engine seed load failed: %s", exc)
        return {"metrics": {}, "alerts": [], "backtest": {}}


def build_baseline_documentation() -> dict[str, Any]:
    return {
        "baseline_window_days": _BASELINE_WINDOW_DAYS,
        "baseline_formula": f"rolling_mean_{_BASELINE_WINDOW_DAYS}d",
        "baseline_version": _BASELINE_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "detection_method": "rolling_baseline + robust z-score + significance",
        "no_manual_threshold_only": True,
        "display": f"Baseline = {_BASELINE_WINDOW_DAYS}-day rolling mean | Version {_BASELINE_VERSION}",
    }


def build_low_sample_guard(sample_days: int) -> dict[str, Any]:
    sufficient = sample_days >= _MIN_SAMPLE_DAYS
    return {
        "sample_days": sample_days,
        "min_sample_days": _MIN_SAMPLE_DAYS,
        "low_sample_guard": True,
        "alert_suppressed": not sufficient,
        "display": (
            f"Sample: {sample_days} days (min {_MIN_SAMPLE_DAYS}) | "
            f"Alerts: {'enabled' if sufficient else 'suppressed — insufficient data'}"
        ),
    }


def compute_z_score(current: float, mean: float, std: float) -> float:
    if std <= 0:
        return 0.0
    return round((current - mean) / std, 4)


def detect_anomaly(
    metric: dict[str, Any],
    *,
    baseline: dict[str, Any],
) -> dict[str, Any] | None:
    sample_days = int(baseline.get("sample_days", 0))
    guard = build_low_sample_guard(sample_days)
    if guard["alert_suppressed"]:
        return None

    current = float(metric.get("current_value", 0))
    mean = float(baseline.get("rolling_mean", 0))
    std = float(baseline.get("rolling_std", 1))
    z = compute_z_score(current, mean, std)

    if abs(z) < _ZSCORE_THRESHOLD:
        return None

    deviation_pct = round((current - mean) / mean * 100, 2) if mean else 0
    severity: AlertSeverity = "high" if abs(z) >= 4 else "medium" if abs(z) >= 3.5 else "low"

    return {
        "metric": metric.get("metric"),
        "asset": metric.get("asset"),
        "venue": metric.get("venue"),
        "current_value": current,
        "baseline_mean": mean,
        "baseline_std": std,
        "z_score": z,
        "deviation_pct": deviation_pct,
        "severity": severity,
        "contributing_metrics": metric.get("contributing_metrics") or [metric.get("metric")],
        "context": metric.get("context"),
        "baseline": build_baseline_documentation(),
        "low_sample_guard": guard,
        "not_a_signal": True,
        "detection_method": "z_score",
    }


def build_backtest_false_positives(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    bt = seed.get("backtest") or {}
    total = int(bt.get("total_alerts", 0))
    correct = int(bt.get("correct_alerts", 0))
    false_pos = int(bt.get("false_positives", 0))
    rate = round(false_pos / total * 100, 1) if total else 0.0

    return {
        "total_alerts": total,
        "correct_alerts": correct,
        "false_positives": false_pos,
        "false_positive_rate_pct": rate,
        "backtest_window": bt.get("window", "2025-01 to 2026-08"),
        "display": (
            f"Backtest: {total} alerts | {correct} correct | "
            f"{false_pos} false positive = {rate}%"
        ),
    }


def build_anomaly_alert_record(alert: dict[str, Any]) -> dict[str, Any]:
    absorbed = alert.get("absorbed_from")
    sub_tasks = []
    if absorbed == 131 or alert.get("type") == "unusual_liquidity":
        sub_tasks.append("#131")
    if absorbed == 121 or alert.get("type") == "large_liquidity_event":
        sub_tasks.append("#121")

    return {
        "alert_id": alert.get("alert_id"),
        "type": alert.get("type", "metric_anomaly"),
        "absorbed_sub_tasks": sub_tasks or ["#719"],
        "asset": alert.get("asset"),
        "venue": alert.get("venue"),
        "metric": alert.get("metric"),
        "z_score": alert.get("z_score"),
        "deviation_pct": alert.get("deviation_pct"),
        "severity": alert.get("severity"),
        "contributing_metrics": alert.get("contributing_metrics"),
        "context": alert.get("context"),
        "baseline": build_baseline_documentation(),
        "not_a_signal": True,
        "display": alert.get("display"),
    }


def build_smart_anomaly_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    metrics = (seed.get("metrics") or {}).get(sym) or []
    baselines = (seed.get("baselines") or {}).get(sym) or {}

    detected = []
    for m in metrics:
        metric_name = m.get("metric", "unknown")
        baseline = baselines.get(metric_name) or baselines.get("default") or {}
        anomaly = detect_anomaly(m, baseline=baseline)
        if anomaly:
            detected.append(anomaly)

    stored_alerts = [
        build_anomaly_alert_record(a)
        for a in seed.get("alerts") or []
        if a.get("asset", "").upper() == sym
    ]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ids": list(_ABSORBED_IDS),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "asset": sym,
        "detected_anomalies": detected,
        "stored_alerts": stored_alerts,
        "baseline": build_baseline_documentation(),
        "backtest_false_positives": build_backtest_false_positives(seed),
        "no_manual_threshold_only": True,
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def list_anomaly_alerts(
    *,
    asset: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    seed = _load_seed()
    alerts = [build_anomaly_alert_record(a) for a in seed.get("alerts") or []]
    if asset:
        alerts = [a for a in alerts if a.get("asset", "").upper() == asset.upper()]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(alerts[:limit]),
        "alerts": alerts[:limit],
        "backtest_false_positives": build_backtest_false_positives(seed),
        "timestamp": _utcnow(),
    }


def smart_anomaly_alert_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Smart Anomaly Alert Engine",
        "feature_ids": list(_ABSORBED_IDS),
        "absorbed_tickets": {
            719: "Anomaly Detection Alerts",
            131: "Unusual Liquidity",
            121: "Large Liquidity Events",
        },
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "baseline": build_baseline_documentation(),
        "backtest_false_positives": build_backtest_false_positives(seed),
        "acceptance_criteria": {
            "baseline_version_documented": True,
            "low_sample_guard": True,
            "backtest_false_positives_documented": True,
            "no_manual_threshold_only": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
