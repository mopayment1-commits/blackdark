"""
Flow Anomaly Detection Module — Feature #282 (Sprint 2 Intelligence Ledger).

Orderflow anomaly detection via rule-based statistical thresholds.
Rule-based first (Z-score, IQR) — ML deferred to Wave 3.

NOT signals — descriptive anomaly alerts with evidence schema.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.FlowAnomalyDetection")

_FEATURE_ID = 282
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Flow Anomaly Detection"
_SPRINT = 2
_SEED_PATH = Path("data/flow_anomaly_detection_seed.json")
_METHODOLOGY_VERSION = "1.0"
_BASELINE_WINDOW_DAYS = 30
_MIN_TRADES_PER_DAY = 1000
_ZSCORE_THRESHOLD = 3.0
_IQR_MULTIPLIER = 1.5

_DISCLAIMER = (
    "Anomaly alerts describe statistical deviations from documented baselines. "
    "Not investment advice. Not trade signals. "
    "Confidence reflects statistical deviation strength — not profit probability."
)

ConfidenceLevel = Literal["low", "medium", "high"]
DetectionMethod = Literal["z_score", "iqr", "both"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"baselines": {}, "alerts": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("flow anomaly detection seed load failed: %s", exc)
        return {"baselines": {}, "alerts": []}


def build_baseline_controls(baseline: dict[str, Any]) -> dict[str, Any]:
    """Baseline/sample controls — 30-day rolling, min 1000 trades/day."""
    trades_per_day = int(baseline.get("trades_per_day", 0))
    window_days = int(baseline.get("window_days", _BASELINE_WINDOW_DAYS))
    sufficient = trades_per_day >= _MIN_TRADES_PER_DAY

    return {
        "asset": baseline.get("asset"),
        "venue": baseline.get("venue"),
        "metric": baseline.get("metric"),
        "window_days": window_days,
        "trades_per_day": trades_per_day,
        "min_trades_per_day": _MIN_TRADES_PER_DAY,
        "baseline_documented": bool(baseline.get("documented", True)),
        "rolling_mean": baseline.get("rolling_mean"),
        "rolling_std": baseline.get("rolling_std"),
        "iqr_q1": baseline.get("iqr_q1"),
        "iqr_q3": baseline.get("iqr_q3"),
        "sample_sufficient": sufficient,
        "detection_enabled": sufficient,
        "display": (
            f"Baseline: {baseline.get('asset')} @ {baseline.get('venue')} | "
            f"{window_days}D rolling | {trades_per_day:,} trades/day | "
            f"Detection: {'enabled' if sufficient else 'disabled (< min sample)'}"
        ),
    }


def compute_z_score(actual: float, mean: float, std: float) -> float:
    if std <= 0:
        return 0.0
    return round((actual - mean) / std, 4)


def compute_iqr_bounds(q1: float, q3: float, *, multiplier: float = _IQR_MULTIPLIER) -> tuple[float, float]:
    iqr = q3 - q1
    return round(q1 - multiplier * iqr, 4), round(q3 + multiplier * iqr, 4)


def build_anomaly_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """Evidence schema — alert with trade_ids/addresses and confidence."""
    deviation_pct = float(alert.get("deviation_pct", 0))
    if abs(deviation_pct) >= 50:
        confidence: ConfidenceLevel = "high"
    elif abs(deviation_pct) >= 25:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "asset": alert.get("asset"),
        "venue": alert.get("venue"),
        "metric": alert.get("metric"),
        "expected_range": alert.get("expected_range"),
        "actual_value": alert.get("actual_value"),
        "deviation_pct": deviation_pct,
        "detection_method": alert.get("detection_method", "z_score"),
        "evidence": {
            "trade_ids": alert.get("trade_ids") or [],
            "addresses": alert.get("addresses") or [],
            "bucket_ids": alert.get("bucket_ids") or [],
        },
        "confidence": confidence,
        "timestamp": alert.get("timestamp"),
        "not_a_signal": True,
        "not_a_recommendation": True,
        "display": (
            f"Anomaly: {alert.get('asset')} @ {alert.get('venue')} | "
            f"{alert.get('metric')}: {alert.get('actual_value')} "
            f"(expected {alert.get('expected_range')}, dev {deviation_pct:+.1f}%) | "
            f"Method: {alert.get('detection_method', 'z_score')} | "
            f"Confidence: {confidence}"
        ),
        "disclaimer": _DISCLAIMER,
    }


def detect_anomaly_from_baseline(
    *,
    actual: float,
    baseline: dict[str, Any],
    method: DetectionMethod = "both",
) -> dict[str, Any] | None:
    """Rule-based anomaly detection — Z-score and/or IQR."""
    controls = build_baseline_controls(baseline)
    if not controls["detection_enabled"]:
        return None

    mean = float(baseline.get("rolling_mean", 0))
    std = float(baseline.get("rolling_std", 1))
    q1 = float(baseline.get("iqr_q1", 0))
    q3 = float(baseline.get("iqr_q3", 0))

    z = compute_z_score(actual, mean, std)
    lower, upper = compute_iqr_bounds(q1, q3)
    z_anomaly = abs(z) >= _ZSCORE_THRESHOLD
    iqr_anomaly = actual < lower or actual > upper

    if method == "z_score" and not z_anomaly:
        return None
    if method == "iqr" and not iqr_anomaly:
        return None
    if method == "both" and not (z_anomaly or iqr_anomaly):
        return None

    detection_method = "both" if z_anomaly and iqr_anomaly else ("z_score" if z_anomaly else "iqr")
    deviation_pct = round((actual - mean) / mean * 100, 2) if mean else 0.0

    return build_anomaly_alert({
        "asset": baseline.get("asset"),
        "venue": baseline.get("venue"),
        "metric": baseline.get("metric"),
        "expected_range": f"{lower} – {upper}" if iqr_anomaly else f"μ±{_ZSCORE_THRESHOLD}σ ({mean:.2f}±{std * _ZSCORE_THRESHOLD:.2f})",
        "actual_value": actual,
        "deviation_pct": deviation_pct,
        "detection_method": detection_method,
        "trade_ids": baseline.get("sample_trade_ids") or [],
        "addresses": baseline.get("sample_addresses") or [],
        "bucket_ids": baseline.get("sample_bucket_ids") or [],
        "timestamp": _utcnow(),
    })


def build_scope_lock() -> dict[str, Any]:
    return {
        "asset_classes": ["spot", "perp"],
        "dex_flow": "separate pipeline",
        "whale_alerts": "separate module",
        "detection_phase_1": "Z-score + IQR (rule-based)",
        "detection_phase_2": "ML anomaly detection (Wave 3)",
        "display": (
            "Spot + perp only | DEX flow = separate | Whale alerts = separate | "
            "Phase 1: Z-score + IQR | Phase 2: ML (Wave 3)"
        ),
    }


def list_anomaly_alerts(
    *,
    asset: str | None = None,
    venue: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    seed = _load_seed()
    alerts = [build_anomaly_alert(a) for a in seed.get("alerts") or []]
    if asset:
        alerts = [a for a in alerts if a.get("asset") == asset.upper()]
    if venue:
        alerts = [a for a in alerts if a.get("venue") == venue]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(alerts[:limit]),
        "alerts": alerts[:limit],
        "timestamp": _utcnow(),
    }


def build_flow_anomaly_panel(asset: str = "BTC") -> dict[str, Any]:
    """Flow anomaly panel with baseline controls and live detection."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    baselines = [
        b for b in (seed.get("baselines") or [])
        if b.get("asset", "").upper() == sym
    ]

    baseline_controls = [build_baseline_controls(b) for b in baselines]
    live_detections: list[dict[str, Any]] = []
    for b in baselines:
        actual = b.get("current_value")
        if actual is not None:
            detected = detect_anomaly_from_baseline(actual=float(actual), baseline=b)
            if detected:
                live_detections.append(detected)

    seed_alerts = [
        a for a in (seed.get("alerts") or [])
        if a.get("asset", "").upper() == sym
    ]
    alerts = [build_anomaly_alert(a) for a in seed_alerts]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "flow_anomaly_detection",
        "asset": sym,
        "baseline_controls": baseline_controls,
        "live_detections": live_detections,
        "alerts": alerts,
        "alert_count": len(alerts) + len(live_detections),
        "scope_lock": build_scope_lock(),
        "rule_based_first": True,
        "ml_deferred_wave_3": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def flow_anomaly_detection_status() -> dict[str, Any]:
    seed = _load_seed()
    baselines = seed.get("baselines") or []
    sufficient = sum(1 for b in baselines if int(b.get("trades_per_day", 0)) >= _MIN_TRADES_PER_DAY)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Flow Anomaly Detection Module",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "scope_lock": build_scope_lock(),
        "baseline_window_days": _BASELINE_WINDOW_DAYS,
        "min_trades_per_day": _MIN_TRADES_PER_DAY,
        "zscore_threshold": _ZSCORE_THRESHOLD,
        "iqr_multiplier": _IQR_MULTIPLIER,
        "baseline_count": len(baselines),
        "sufficient_sample_count": sufficient,
        "acceptance_criteria": {
            "baseline_sample_controls": True,
            "evidence_schema": True,
            "rule_based_first": True,
            "ml_deferred_wave_3": True,
            "spot_perp_only": True,
        },
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
