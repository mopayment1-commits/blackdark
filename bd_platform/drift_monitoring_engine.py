"""
Drift Monitoring Engine — Features #209 + #213 (Sprint 0/1, merged).

Market/data drift detection with versioned baselines, false-alarm review,
separation of data gaps from distribution drift, and no automatic promotion.
Human review required for all drift actions.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DriftMonitoring")

_FEATURE_ID = 209
_MERGED_FEATURES = [209, 213]
_SEED_PATH = Path("data/drift_baselines_seed.json")
_STORE_PATH = Path("data/drift_monitoring.json")
_ALERTS_PATH = Path("data/drift_alerts.jsonl")

Severity = Literal["low", "medium", "high"]
Persistence = Literal["1_hour", "1_day", "1_week"]
AlertType = Literal["distribution_drift", "data_gap", "stale_data"]
ReviewStatus = Literal["pending", "confirmed", "false_alarm", "dismissed"]

_PSI_THRESHOLD_LOW = 0.10
_PSI_THRESHOLD_MEDIUM = 0.20
_PSI_THRESHOLD_HIGH = 0.35


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"baselines": [], "sample_current": {}, "sample_stale": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("drift baselines seed load failed: %s", exc)
        return {"baselines": [], "sample_current": {}, "sample_stale": {}}


def _load_store() -> dict[str, Any]:
    if _STORE_PATH.is_file():
        try:
            return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    seed = _load_seed()
    store = {
        "baselines": {b["version"]: b for b in seed.get("baselines") or []},
        "active_baseline_version": "v2.1",
        "reviews": {},
        "updated_at": _utcnow(),
    }
    _save_store(store)
    return store


def _save_store(blob: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    blob["updated_at"] = _utcnow()
    _STORE_PATH.write_text(json.dumps(blob, indent=2, ensure_ascii=False), encoding="utf-8")


def _append_alert(alert: dict[str, Any]) -> None:
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _ALERTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(alert, ensure_ascii=False) + "\n")


def _baseline_display(baseline: dict[str, Any]) -> str:
    return (
        f"Baseline {baseline.get('version')} | "
        f"Window: {baseline.get('window_days')} days | "
        f"Updated: {baseline.get('updated_at')}"
    )


def _deterministic_psi(reference_mean: float, reference_std: float, current: float) -> float:
    """Deterministic PSI proxy — z-score distance normalized to [0, 1]."""
    std = max(reference_std, 1e-6)
    z = abs(current - reference_mean) / std
    psi = min(1.0, z / 4.0)
    return round(psi, 4)


def _classify_severity(psi: float) -> Severity:
    if psi >= _PSI_THRESHOLD_HIGH:
        return "high"
    if psi >= _PSI_THRESHOLD_MEDIUM:
        return "medium"
    return "low"


def _severity_persistence(severity: Severity) -> Persistence:
    mapping: dict[Severity, Persistence] = {
        "low": "1_hour",
        "medium": "1_day",
        "high": "1_week",
    }
    return mapping[severity]


def _alert_id(feature: str, baseline_version: str, alert_type: str) -> str:
    raw = f"{feature}|{baseline_version}|{alert_type}".encode()
    return hashlib.sha256(raw).hexdigest()[:12]


def _detect_stale_or_gap(values: dict[str, Any]) -> list[dict[str, Any]]:
    """Separate missing/stale data from distribution drift."""
    alerts: list[dict[str, Any]] = []
    null_features = [k for k, v in values.items() if v is None and not k.startswith("stale")]
    if null_features:
        alerts.append({
            "alert_type": "data_gap",
            "features": null_features,
            "severity": "high",
            "persistence": "1_day",
            "display": f"Data Gap | Missing: {', '.join(null_features)}",
            "is_drift": False,
            "human_review_required": True,
        })
    if values.get("stale_since"):
        alerts.append({
            "alert_type": "stale_data",
            "stale_since": values["stale_since"],
            "severity": "medium",
            "persistence": "1_hour",
            "display": f"Stale Data | Since: {values['stale_since']}",
            "is_drift": False,
            "human_review_required": True,
        })
    return alerts


def detect_drift(
    current_values: dict[str, Any],
    *,
    baseline_version: str | None = None,
    model_id: str = "oracle_signal_v3",
) -> dict[str, Any]:
    """Deterministic drift detection against versioned baseline."""
    store = _load_store()
    version = baseline_version or store.get("active_baseline_version") or "v2.1"
    baseline = (store.get("baselines") or {}).get(version)
    if not baseline:
        return {"ok": False, "error": "baseline_not_found", "version": version}

    gap_alerts = _detect_stale_or_gap(current_values)
    drift_alerts: list[dict[str, Any]] = []
    features = baseline.get("features") or {}

    for feature, bounds in features.items():
        current = current_values.get(feature)
        if current is None:
            continue
        if not isinstance(current, (int, float)) or not math.isfinite(float(current)):
            continue
        psi = _deterministic_psi(
            float(bounds["mean"]),
            float(bounds["std"]),
            float(current),
        )
        if psi < _PSI_THRESHOLD_LOW:
            continue
        severity = _classify_severity(psi)
        persistence = _severity_persistence(severity)
        alert = {
            "alert_id": _alert_id(feature, version, "distribution_drift"),
            "alert_type": "distribution_drift",
            "feature": feature,
            "psi": psi,
            "severity": severity,
            "persistence": persistence,
            "baseline_version": version,
            "model_id": model_id,
            "display": (
                f"Distribution Drift | {feature} | PSI: {psi} | "
                f"Severity: {severity.title()} | Persistence: {persistence.replace('_', ' ')}"
            ),
            "is_drift": True,
            "human_review_required": True,
            "auto_action": None,
            "review_status": "pending",
        }
        drift_alerts.append(alert)
        _append_alert(alert)

    all_alerts = gap_alerts + drift_alerts
    retraining = _retraining_recommendation(model_id, drift_alerts)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_features": _MERGED_FEATURES,
        "baseline_display": _baseline_display(baseline),
        "baseline_version": version,
        "model_id": model_id,
        "drift_detected": bool(drift_alerts),
        "data_gap_detected": bool(gap_alerts),
        "alerts": all_alerts,
        "drift_alerts": drift_alerts,
        "gap_alerts": gap_alerts,
        "deterministic": True,
        "no_automatic_promotion": True,
        "human_review_required": True,
        "retraining_trigger": retraining,
        "timestamp": _utcnow(),
    }


def _retraining_recommendation(model_id: str, drift_alerts: list[dict[str, Any]]) -> dict[str, Any]:
    high = [a for a in drift_alerts if a.get("severity") == "high"]
    if high:
        return {
            "model_id": model_id,
            "display": f"Model {model_id} drift detected | Recommended: Review | Not: Auto-retrain",
            "recommended_action": "review",
            "auto_retrain": False,
            "human_review_required": True,
        }
    if drift_alerts:
        return {
            "model_id": model_id,
            "display": f"Model {model_id} minor drift | Recommended: Monitor | Not: Auto-retrain",
            "recommended_action": "monitor",
            "auto_retrain": False,
            "human_review_required": True,
        }
    return {
        "model_id": model_id,
        "display": f"Model {model_id} | No drift detected",
        "recommended_action": "none",
        "auto_retrain": False,
    }


def review_drift_alert(
    alert_id: str,
    *,
    decision: ReviewStatus,
    reviewer: str,
    notes: str = "",
) -> dict[str, Any]:
    """False-alarm review — every drift alert reviewed before action."""
    store = _load_store()
    reviews = store.setdefault("reviews", {})
    reviews[alert_id] = {
        "alert_id": alert_id,
        "decision": decision,
        "reviewer": reviewer,
        "notes": notes,
        "reviewed_at": _utcnow(),
        "false_alarm_review": decision == "false_alarm",
    }
    _save_store(store)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "alert_id": alert_id,
        "review": reviews[alert_id],
        "display": f"Alert {alert_id} | Review: {decision} | Reviewer: {reviewer}",
        "no_automatic_promotion": True,
        "timestamp": _utcnow(),
    }


def list_baselines() -> dict[str, Any]:
    store = _load_store()
    baselines = list((store.get("baselines") or {}).values())
    for b in baselines:
        b["display"] = _baseline_display(b)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "versioned_baselines": True,
        "active_version": store.get("active_baseline_version"),
        "baselines": baselines,
        "timestamp": _utcnow(),
    }


def get_baseline(version: str) -> dict[str, Any]:
    store = _load_store()
    baseline = (store.get("baselines") or {}).get(version)
    if not baseline:
        return {"ok": False, "error": "baseline_not_found"}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "baseline": {**baseline, "display": _baseline_display(baseline)},
        "timestamp": _utcnow(),
    }


def get_drift_dashboard(*, model_id: str = "oracle_signal_v3") -> dict[str, Any]:
    seed = _load_seed()
    current = detect_drift(seed.get("sample_current") or {}, model_id=model_id)
    stale = detect_drift(seed.get("sample_stale") or {}, model_id=model_id)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_features": _MERGED_FEATURES,
        "model_id": model_id,
        "current_sample": current,
        "stale_sample": stale,
        "data_gap_separated_from_drift": True,
        "false_alarm_review_required": True,
        "no_automatic_promotion": True,
        "timestamp": _utcnow(),
    }


def run_reproducible_drift_test() -> dict[str, Any]:
    """Reproducible deterministic drift test — same input → same output."""
    seed = _load_seed()
    values = seed.get("sample_current") or {}
    run_a = detect_drift(values)
    run_b = detect_drift(values)
    checksum_a = hashlib.sha256(json.dumps(run_a["alerts"], sort_keys=True).encode()).hexdigest()[:16]
    checksum_b = hashlib.sha256(json.dumps(run_b["alerts"], sort_keys=True).encode()).hexdigest()[:16]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "reproducible": checksum_a == checksum_b,
        "checksum": checksum_a,
        "run_count": 2,
        "deterministic": True,
        "timestamp": _utcnow(),
    }


def drift_monitoring_status() -> dict[str, Any]:
    store = _load_store()
    baselines = store.get("baselines") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_features": _MERGED_FEATURES,
        "module": "Drift Monitoring Engine",
        "sprint": "0/1",
        "baseline_count": len(baselines),
        "active_baseline_version": store.get("active_baseline_version"),
        "versioned_baselines": True,
        "false_alarm_review": True,
        "data_gap_separated_from_drift": True,
        "reproducible_tests": True,
        "no_automatic_promotion": True,
        "human_review_required": True,
        "severity_levels": ["low", "medium", "high"],
        "persistence_rules": ["1_hour", "1_day", "1_week"],
        "retraining_policy": "Recommended: Review | Not: Auto-retrain",
        "sla": {"response_seconds": 2, "accuracy_target_pct": 95, "uptime_target_pct": 99},
        "timestamp": _utcnow(),
    }
