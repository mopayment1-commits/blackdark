"""Decision Calibration Ledger (DTS-021, DTS-059)."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

METHODOLOGY_VERSION = "dts-p4-calibration-1.0"
_MIN_SAMPLES = 5
_LEDGER_PATH = Path(__file__).resolve().parent.parent / "data" / "decision_calibration_ledger.jsonl"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_rows() -> list[dict[str, Any]]:
    if not _LEDGER_PATH.exists():
        return []
    rows = []
    for line in _LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def append_calibration_observation(row: dict[str, Any]) -> dict[str, Any]:
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def evaluate_calibration(
    payload: dict[str, Any],
    *,
    evidence_class: str | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Compute calibration context; fail closed on insufficient data."""
    rows = _load_rows()
    if payload.get("calibration_observations"):
        for obs in payload["calibration_observations"]:
            append_calibration_observation({**obs, "methodology_version": METHODOLOGY_VERSION})

    window_rows = [r for r in rows if not evidence_class or r.get("evidence_class") == evidence_class]
    if len(window_rows) < _MIN_SAMPLES:
        return {
            "state": "CALIBRATION_INSUFFICIENT_DATA",
            "sample_size": len(window_rows),
            "min_samples_required": _MIN_SAMPLES,
            "confidence_display": "CALIBRATION_INSUFFICIENT_DATA",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    buckets: dict[str, list[float]] = {}
    for row in window_rows:
        bucket = str(row.get("confidence_bucket") or "unknown")
        outcome = row.get("realized_success")
        if outcome is None:
            continue
        buckets.setdefault(bucket, []).append(1.0 if bool(outcome) else 0.0)

    bucket_stats = []
    for bucket, outcomes in sorted(buckets.items()):
        freq = sum(outcomes) / len(outcomes)
        bucket_stats.append({"bucket": bucket, "realized_frequency": round(freq, 4), "n": len(outcomes)})

    declared = confidence if confidence is not None else _optional_float(payload.get("confidence_percent"))
    brier = _brier_score(window_rows)
    calibration_error = _mean_calibration_error(window_rows)
    weak = calibration_error is not None and calibration_error > 0.15

    state = "CALIBRATION_WEAK" if weak else "AVAILABLE"
    return {
        "state": state,
        "sample_size": len(window_rows),
        "confidence_buckets": bucket_stats,
        "brier_score": brier,
        "calibration_error": calibration_error,
        "base_rate": round(sum(1 for r in window_rows if r.get("realized_success")) / len(window_rows), 4),
        "abstention_adjusted": bool(payload.get("abstention_count")),
        "evidence_class": evidence_class,
        "time_window": payload.get("calibration_time_window") or "ledger_all",
        "confidence_display": state if weak or brier is None else "CALIBRATION_ADJUSTED",
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
    }


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _brier_score(rows: list[dict[str, Any]]) -> float | None:
    pairs = []
    for row in rows:
        p = _optional_float(row.get("declared_probability"))
        y = row.get("realized_success")
        if p is None or y is None:
            continue
        y_val = 1.0 if bool(y) else 0.0
        pairs.append((p, y_val))
    if not pairs:
        return None
    return round(sum((p - y) ** 2 for p, y in pairs) / len(pairs), 6)


def _mean_calibration_error(rows: list[dict[str, Any]]) -> float | None:
    errors = []
    for row in rows:
        p = _optional_float(row.get("declared_probability"))
        y = row.get("realized_success")
        if p is None or y is None:
            continue
        errors.append(abs(p - (1.0 if bool(y) else 0.0)))
    if not errors:
        return None
    return round(sum(errors) / len(errors), 6)
