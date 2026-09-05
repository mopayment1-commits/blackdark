"""
BLACKDARK — Data drift, OOD detection, and confidence calibration.

Guards against model collapse on unseen market regimes (due-diligence critical).
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import config
from ml.training_utils import FEATURE_COLUMNS

logger = logging.getLogger("BLACKDARK.MLDrift")

# Re-export for backward compatibility — leak-prone columns intentionally removed.


def _envelope_path() -> Path:
    return config.ML_MODELS_DIR / "feature_envelope.json"


def _calibration_path() -> Path:
    return config.ML_MODELS_DIR / "confidence_calibration.json"


def _features_from_row(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("features_json")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    if isinstance(raw, dict):
        return raw
    return {}


def build_feature_envelope(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Min/max/mean/std per feature from labeled training rows."""
    import statistics

    buckets: dict[str, list[float]] = {col: [] for col in FEATURE_COLUMNS}
    for row in rows:
        feats = _features_from_row(row)
        for col in FEATURE_COLUMNS:
            val = feats.get(col)
            if isinstance(val, (int, float)) and math.isfinite(float(val)):
                buckets[col].append(float(val))

    envelope: dict[str, Any] = {}
    for col, values in buckets.items():
        if len(values) < 3:
            continue
        mean = statistics.fmean(values)
        stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
        envelope[col] = {
            "min": min(values),
            "max": max(values),
            "mean": mean,
            "std": max(stdev, 1e-6),
            "n": len(values),
        }
    return {
        "feature_columns": list(FEATURE_COLUMNS),
        "features": envelope,
        "sample_count": len(rows),
    }


def save_feature_envelope(envelope: dict[str, Any]) -> Path:
    config.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = _envelope_path()
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    return path


def load_feature_envelope() -> dict[str, Any] | None:
    path = _envelope_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def ood_score(features: dict[str, Any], envelope: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fraction of features outside training min/max (with 2σ slack)."""
    env = envelope or load_feature_envelope()
    fail_closed = getattr(config, "ML_OOD_FAIL_CLOSED", True)
    if not env or not env.get("features"):
        if fail_closed:
            return {
                "score": 1.0,
                "is_ood": True,
                "reason": "no_envelope_fail_closed",
                "out_of_range": ["envelope_missing"],
                "features_checked": 0,
                "threshold": float(getattr(config, "ML_OOD_REJECT_THRESHOLD", 0.65)),
            }
        return {"score": 0.0, "is_ood": False, "reason": "no_envelope", "out_of_range": []}

    out_of_range: list[str] = []
    checked = 0
    for col, bounds in env["features"].items():
        val = features.get(col)
        if not isinstance(val, (int, float)) or not math.isfinite(float(val)):
            continue
        checked += 1
        val_f = float(val)
        lo = float(bounds["min"]) - 2.0 * float(bounds["std"])
        hi = float(bounds["max"]) + 2.0 * float(bounds["std"])
        if val_f < lo or val_f > hi:
            out_of_range.append(col)

    score = (len(out_of_range) / checked) if checked else 0.0
    threshold = float(getattr(config, "ML_OOD_REJECT_THRESHOLD", 0.65))
    return {
        "score": round(score, 4),
        "is_ood": score >= threshold,
        "out_of_range": out_of_range,
        "features_checked": checked,
        "threshold": threshold,
    }


def _reference_quantile_edges(reference: list[float], *, bins: int) -> list[float]:
    """OECD-style bin edges from reference distribution only (quantile breakpoints)."""
    ref = sorted(reference)
    n = len(ref)
    edges: list[float] = []
    for i in range(bins + 1):
        idx = min(int(i * n / bins), n - 1)
        edges.append(float(ref[idx]))
    # Ensure strictly increasing edges for stable bucket assignment.
    for i in range(1, len(edges)):
        if edges[i] <= edges[i - 1]:
            edges[i] = edges[i - 1] + 1e-9
    return edges


def _psi_from_edges(reference: list[float], current: list[float], edges: list[float]) -> float:
    if len(edges) < 2:
        return 0.0
    bins = len(edges) - 1
    psi = 0.0
    for i in range(bins):
        b_lo, b_hi = edges[i], edges[i + 1]
        ref_pct = sum(
            1 for x in reference if (b_lo <= x < b_hi) or (i == bins - 1 and x == b_hi)
        ) / len(reference)
        cur_pct = sum(
            1 for x in current if (b_lo <= x < b_hi) or (i == bins - 1 and x == b_hi)
        ) / len(current)
        ref_pct = max(ref_pct, 1e-6)
        cur_pct = max(cur_pct, 1e-6)
        psi += (cur_pct - ref_pct) * math.log(cur_pct / ref_pct)
    return round(abs(psi), 4)


def compute_psi(
    reference: list[float],
    current: list[float],
    *,
    bins: int = 5,
    reference_bins: bool = True,
) -> float:
    """Population Stability Index.

    When reference_bins=True (default), bin edges are derived from the reference
    distribution only (OECD composite-indicator practice). When False, uses the
    legacy combined min/max equal-width bins for backward compatibility.
    """
    if len(reference) < 5 or len(current) < 5:
        return 0.0

    if reference_bins:
        edges = _reference_quantile_edges(reference, bins=bins)
        return _psi_from_edges(reference, current, edges)

    ref = sorted(reference)
    cur = sorted(current)
    lo = min(ref[0], cur[0])
    hi = max(ref[-1], cur[-1])
    if hi <= lo:
        return 0.0

    width = (hi - lo) / bins
    psi = 0.0
    for i in range(bins):
        b_lo = lo + i * width
        b_hi = b_lo + width
        ref_pct = sum(1 for x in ref if b_lo <= x < b_hi or (i == bins - 1 and x == b_hi)) / len(ref)
        cur_pct = sum(1 for x in cur if b_lo <= x < b_hi or (i == bins - 1 and x == b_hi)) / len(cur)
        ref_pct = max(ref_pct, 1e-6)
        cur_pct = max(cur_pct, 1e-6)
        psi += (cur_pct - ref_pct) * math.log(cur_pct / ref_pct)
    return round(abs(psi), 4)


def drift_report(
    reference_rows: list[dict[str, Any]],
    current_features: list[dict[str, Any]],
    *,
    reference_bins: bool = True,
) -> dict[str, Any]:
    """PSI per feature between training reference and live batch."""
    threshold = float(getattr(config, "ML_DRIFT_PSI_THRESHOLD", 0.25))
    alerts: list[dict[str, Any]] = []

    for col in FEATURE_COLUMNS:
        ref_vals = _extract_feature_values(reference_rows, col)
        cur_vals = [float(f[col]) for f in current_features if isinstance(f.get(col), (int, float))]
        if len(ref_vals) < 5 or len(cur_vals) < 5:
            continue
        psi = compute_psi(ref_vals, cur_vals, reference_bins=reference_bins)
        if psi >= threshold:
            alerts.append({"feature": col, "psi": psi, "severity": "high" if psi >= threshold * 2 else "medium"})

    return {
        "drift_detected": bool(alerts),
        "alerts": alerts,
        "psi_threshold": threshold,
        "features_checked": len(FEATURE_COLUMNS),
        "binning": "reference_quantile" if reference_bins else "combined_minmax_equal_width",
    }


def _extract_feature_values(rows: list[dict[str, Any]], col: str) -> list[float]:
    out: list[float] = []
    for row in rows:
        raw = row.get("features_json")
        feats = json.loads(raw) if isinstance(raw, str) else (raw or {})
        val = feats.get(col, row.get(col))
        if isinstance(val, (int, float)):
            out.append(float(val))
    return out


def build_confidence_calibration(labeled_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Map heuristic confidence buckets → empirical hit rate."""
    buckets: dict[str, list[int]] = {}
    for row in labeled_rows:
        conf = int(row.get("confidence") or 0)
        bucket = f"{(conf // 10) * 10}-{(conf // 10) * 10 + 9}"
        label = str(row.get("label") or row.get("outcome") or "")
        buckets.setdefault(bucket, []).append(1 if label == "correct" else 0)

    calibration: dict[str, Any] = {}
    for bucket, outcomes in buckets.items():
        if not outcomes:
            continue
        calibration[bucket] = {
            "samples": len(outcomes),
            "hit_rate": round(sum(outcomes) / len(outcomes), 4),
        }

    payload = {"buckets": calibration, "sample_count": len(labeled_rows)}
    config.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    _calibration_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def calibrate_confidence(raw_percent: float) -> dict[str, Any]:
    """Return calibrated hit-rate estimate for a raw heuristic confidence."""
    path = _calibration_path()
    if not path.exists():
        return {
            "raw_percent": raw_percent,
            "calibrated_hit_rate_percent": raw_percent,
            "calibrated": False,
            "note": "insufficient_calibration_data",
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"raw_percent": raw_percent, "calibrated_hit_rate_percent": raw_percent, "calibrated": False}

    bucket_key = f"{(int(raw_percent) // 10) * 10}-{(int(raw_percent) // 10) * 10 + 9}"
    bucket = (payload.get("buckets") or {}).get(bucket_key)
    if not bucket:
        return {"raw_percent": raw_percent, "calibrated_hit_rate_percent": raw_percent, "calibrated": False}

    hit = float(bucket["hit_rate"]) * 100.0
    return {
        "raw_percent": raw_percent,
        "calibrated_hit_rate_percent": round(hit, 1),
        "calibrated": True,
        "bucket": bucket_key,
        "bucket_samples": bucket.get("samples"),
    }


def validate_model_deployment(
    new_metrics: dict[str, Any],
    *,
    incumbent_metrics: dict[str, Any] | None = None,
    min_accuracy: float = 0.45,
    cold_start_min_accuracy: float = 0.34,
    max_regression: float = 0.05,
) -> dict[str, Any]:
    """Reject new model if accuracy regresses vs incumbent."""
    new_acc = float(new_metrics.get("accuracy") or 0)
    old_acc = float((incumbent_metrics or {}).get("accuracy") or 0)
    # Cold start / weak incumbent: 3-class random ~0.33.
    weak_incumbent = (not incumbent_metrics) or old_acc < float(min_accuracy)
    effective_min = float(cold_start_min_accuracy) if weak_incumbent else float(min_accuracy)
    if new_acc < effective_min:
        return {
            "approved": False,
            "reason": "below_minimum_accuracy",
            "new_accuracy": new_acc,
            "minimum_accuracy": effective_min,
            "cold_start": weak_incumbent,
        }

    if incumbent_metrics and old_acc > 0 and new_acc < old_acc - max_regression:
        return {
            "approved": False,
            "reason": "accuracy_regression",
            "new_accuracy": new_acc,
            "incumbent_accuracy": old_acc,
            "max_regression": max_regression,
        }

    return {"approved": True, "new_accuracy": new_acc, "cold_start": weak_incumbent}


def enforce_drift_actions(report: dict[str, Any]) -> dict[str, Any]:
    """Freeze trading when high-severity PSI drift is detected."""
    if not report.get("drift_detected"):
        return {"action": "none", "drift_detected": False}

    alerts = list(report.get("alerts") or [])
    high = [a for a in alerts if str(a.get("severity") or "") == "high"]
    if not high:
        return {"action": "warn", "drift_detected": True, "alerts": alerts}

    top = high[0]
    feature = str(top.get("feature") or "unknown")
    psi = float(top.get("psi") or 0)
    duration = int(getattr(config, "ML_DRIFT_FREEZE_SEC", 300))
    from risk_manager import freeze_trading

    freeze = freeze_trading(
        f"ml_drift_high:{feature}:psi={psi:.3f}",
        duration_sec=duration,
    )
    logger.warning(
        "ML drift freeze triggered | feature=%s psi=%.3f duration=%ss",
        feature,
        psi,
        duration,
    )
    return {
        "action": "freeze_trading",
        "drift_detected": True,
        "alerts": alerts,
        "freeze": freeze,
    }
