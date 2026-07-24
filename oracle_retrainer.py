"""
BLACKDARK — Reinforcement Learning Retraining Loop (Point 47, lite).

Uses resolved oracle prediction audits to nudge multi-modal dimension weights.
No heavy ML — deterministic error-driven adjustment with encrypted persistence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from database import fetch_oracle_audit_stats
from weight_aggregator import DEFAULT_DIMENSIONS, get_dimension_weights, persist_dimension_weights

logger = logging.getLogger("BLACKDARK.OracleRetrainer")

_LEARNING_RATE = 0.02
_MIN_SAMPLES = 5


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _verdict_bucket(row: dict[str, Any]) -> str:
    verdict = str(row.get("verdict") or row.get("oracle_verdict") or "").lower()
    if "buy" in verdict:
        return "buy"
    if "touch" in verdict or "avoid" in verdict or "sell" in verdict:
        return "avoid"
    outcome = str(row.get("outcome") or "").lower()
    if outcome in {"correct", "hit", "win"}:
        return "buy"
    if outcome in {"miss", "wrong", "loss"}:
        return "avoid"
    return "neutral"


def _price_direction(row: dict[str, Any]) -> str:
    try:
        before = float(row.get("price_at_prediction") or row.get("price") or 0)
        after = float(row.get("price_after_24h") or 0)
    except (TypeError, ValueError):
        return "flat"
    if before <= 0 or after <= 0:
        return "flat"
    change_pct = (after - before) / before * 100
    if change_pct > 0.35:
        return "up"
    if change_pct < -0.35:
        return "down"
    return "flat"


async def run_oracle_retrain_step() -> dict[str, Any]:
    audit = await fetch_oracle_audit_stats(limit=200)
    resolved_rows = [
        row for row in audit.get("recent", [])
        if row.get("resolved") in (1, True, "1")
    ]
    if len(resolved_rows) < _MIN_SAMPLES:
        return {
            "adjusted": False,
            "reason": "insufficient_resolved_samples",
            "resolved_samples": len(resolved_rows),
            "minimum_required": _MIN_SAMPLES,
            "timestamp": _utcnow_iso(),
        }

    dims = get_dimension_weights()
    errors = {"technical": 0.0, "onchain": 0.0, "sentiment": 0.0, "macro": 0.0, "whale": 0.0}
    counts = {k: 0 for k in errors}

    for row in resolved_rows:
        accuracy = float(row.get("accuracy_score") or 0)
        if accuracy >= 70:
            continue

        bucket = _verdict_bucket(row)
        direction = _price_direction(row)
        wrong_buy = bucket == "buy" and direction == "down"
        wrong_avoid = bucket == "avoid" and direction == "up"
        if not (wrong_buy or wrong_avoid):
            continue

        # Under-weight sentiment/onchain when directional calls miss; boost technical.
        errors["sentiment"] += 1.0
        errors["onchain"] += 0.5
        errors["technical"] -= 0.5
        for key in counts:
            counts[key] += 1

    total_errors = sum(errors.values())
    if total_errors <= 0:
        return {
            "adjusted": False,
            "reason": "no_actionable_errors",
            "resolved_samples": len(resolved_rows),
            "average_accuracy_percent": audit.get("average_accuracy_percent", 0),
            "timestamp": _utcnow_iso(),
        }

    new_dims = dict(DEFAULT_DIMENSIONS)
    new_dims.update(dims)
    for key, err in errors.items():
        if counts[key] <= 0:
            continue
        delta = -err * _LEARNING_RATE / max(counts[key], 1)
        new_dims[key] = max(0.05, new_dims.get(key, 0.1) + delta)

    payload = persist_dimension_weights(
        new_dims,
        note=f"auto-retrain from {len(resolved_rows)} resolved predictions",
    )
    logger.info(
        "Oracle retrain adjusted weights | accuracy=%s samples=%s",
        audit.get("average_accuracy_percent"),
        len(resolved_rows),
    )
    return {
        "adjusted": True,
        "resolved_samples": len(resolved_rows),
        "average_accuracy_percent": audit.get("average_accuracy_percent", 0),
        "previous_dimensions": dims,
        "new_dimensions": payload["dimensions"],
        "error_counts": counts,
        "timestamp": _utcnow_iso(),
    }
