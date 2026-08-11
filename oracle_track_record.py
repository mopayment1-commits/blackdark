"""
BLACKDARK — Automatic Oracle Track Record bridge.

Every insert_oracle_prediction / resolve_oracle_prediction writes to the
immutable hash chain — zero manual steps required.
"""

from __future__ import annotations

import logging
from typing import Any

from log_safety import sanitize_asset, sanitize_log_value
from oracle_audit_chain import append_prediction_record, chain_summary, verify_chain

logger = logging.getLogger("BLACKDARK.TrackRecord")


def on_prediction_created(
    prediction_id: int,
    *,
    asset: str,
    price_at_prediction: float,
    verdict: str,
    opportunity_score: int = 0,
    confidence: int = 0,
    source: str = "oracle",
    kind: str | None = None,
) -> dict[str, Any]:
    entry = append_prediction_record({
        "event": "prediction_created",
        "prediction_id": prediction_id,
        "asset": asset.upper(),
        "verdict": verdict.upper(),
        "price_at_prediction": price_at_prediction,
        "opportunity_score": opportunity_score,
        "confidence": confidence,
        "source": source,
        "kind": kind,
        "resolved": False,
    })
    logger.debug(
        "Track record | new prediction id=%s asset=%s",
        sanitize_log_value(prediction_id),
        sanitize_asset(asset),
    )
    return entry


def on_prediction_resolved(
    prediction_id: int,
    *,
    asset: str,
    verdict: str,
    price_at_prediction: float,
    price_after: float,
    outcome: str,
    accuracy_score: float,
    label: str | None = None,
    direction_label: str | None = None,
) -> dict[str, Any]:
    entry = append_prediction_record({
        "event": "prediction_resolved",
        "prediction_id": prediction_id,
        "asset": asset.upper(),
        "verdict": verdict.upper(),
        "price_at_prediction": price_at_prediction,
        "price_after_24h": price_after,
        "outcome": outcome,
        "label": label or outcome,
        "direction_label": direction_label,
        "accuracy_score": round(accuracy_score, 2),
        "resolved": True,
    })
    logger.debug(
        "Track record | resolved id=%s asset=%s outcome=%s acc=%.1f",
        sanitize_log_value(prediction_id),
        sanitize_asset(asset),
        sanitize_log_value(outcome, max_len=24),
        accuracy_score,
    )
    return entry


async def backfill_from_database(*, limit: int = 5000) -> dict[str, Any]:
    """One-time sync: export existing oracle_predictions into hash chain."""
    from database import fetch_labeled_oracle_predictions, fetch_unresolved_oracle_predictions

    created = 0
    resolved = 0

    unresolved = await fetch_unresolved_oracle_predictions(limit=limit)
    for pred in unresolved:
        on_prediction_created(
            int(pred["id"]),
            asset=str(pred.get("asset") or ""),
            price_at_prediction=float(pred.get("price_at_prediction") or 0),
            verdict=str(pred.get("verdict") or "WAIT"),
            opportunity_score=int(pred.get("opportunity_score") or 0),
            confidence=int(pred.get("confidence") or 0),
            source=str(pred.get("source") or "oracle"),
            kind=pred.get("kind"),
        )
        created += 1

    labeled = await fetch_labeled_oracle_predictions(limit=limit, include_synthetic=True)
    seen_ids = {int(p["id"]) for p in unresolved}
    for pred in labeled:
        pid = int(pred["id"])
        if pid not in seen_ids:
            on_prediction_created(
                pid,
                asset=str(pred.get("asset") or ""),
                price_at_prediction=float(pred.get("price_at_prediction") or 0),
                verdict=str(pred.get("verdict") or "WAIT"),
                opportunity_score=int(pred.get("opportunity_score") or 0),
                confidence=int(pred.get("confidence") or 0),
                source=str(pred.get("source") or "oracle"),
                kind=pred.get("kind"),
            )
            created += 1
        if pred.get("resolved"):
            on_prediction_resolved(
                pid,
                asset=str(pred.get("asset") or ""),
                verdict=str(pred.get("verdict") or "WAIT"),
                price_at_prediction=float(pred.get("price_at_prediction") or 0),
                price_after=float(pred.get("price_after_24h") or pred.get("price_at_prediction") or 0),
                outcome=str(pred.get("outcome") or pred.get("label") or "unknown"),
                accuracy_score=float(pred.get("accuracy_score") or 0),
                label=pred.get("label"),
                direction_label=pred.get("direction_label"),
            )
            resolved += 1

    summary = chain_summary()
    return {
        "backfilled_created": created,
        "backfilled_resolved": resolved,
        "chain_records": summary["total_records"],
        "integrity_valid": summary["integrity"]["valid"],
    }


def public_track_record() -> dict[str, Any]:
    """Buyer-facing cumulative stats from immutable chain (live-only primary metrics)."""
    from oracle_integrity import is_synthetic_prediction

    summary = chain_summary(limit=50)
    verify = verify_chain()

    all_resolved = [
        r for r in _read_all_records()
        if r.get("event") == "prediction_resolved" or r.get("resolved") is True
    ]
    live_resolved = [r for r in all_resolved if not is_synthetic_prediction(r)]
    synthetic_resolved = [r for r in all_resolved if is_synthetic_prediction(r)]

    def _label(row: dict) -> str:
        return str(row.get("label") or row.get("outcome") or "").strip().lower()

    def _hit_rate(rows: list[dict]) -> float:
        """Strict hit rate: only full `correct` counts (partial is disclosed separately)."""
        if not rows:
            return 0.0
        correct = sum(1 for r in rows if _label(r) == "correct")
        return round(correct / len(rows) * 100, 2)

    def _partial_rate(rows: list[dict]) -> float:
        if not rows:
            return 0.0
        partial = sum(1 for r in rows if _label(r) == "partial")
        return round(partial / len(rows) * 100, 2)

    live_hit = _hit_rate(live_resolved)
    synth_hit = _hit_rate(synthetic_resolved)
    live_partial = _partial_rate(live_resolved)

    return {
        "immutable_chain": {
            "valid": verify["valid"],
            "total_records": verify["records"],
            "chain_path": verify.get("chain_path"),
        },
        "cumulative": {
            "resolved_predictions": len(live_resolved),
            "hit_rate_percent": live_hit,
            "partial_rate_percent": live_partial,
            "hit_definition": "correct_only",
            "metrics_scope": "live_only",
            "meets_target": live_hit >= 65.0 if len(live_resolved) >= 30 else None,
            "note": (
                "Live predictions only — synthetic historical_seed excluded. "
                "Hit rate counts full correct only; partial is separate."
            ),
        },
        "synthetic_demo_data": {
            "resolved_predictions": len(synthetic_resolved),
            "hit_rate_percent": synth_hit,
            "hit_definition": "correct_only",
            "excluded_from_primary_metrics": True,
            "note": "Due-diligence backfill — not live trading performance.",
        },
        "recent": [
            r for r in (summary.get("recent_records") or [])[-10:]
            if not is_synthetic_prediction(r)
        ],
        "auto_accumulation": True,
        "note": "Every live oracle prediction auto-appends to hash chain on create + resolve.",
    }


def _read_all_records() -> list[dict]:
    import json

    from oracle_audit_chain import CHAIN_PATH

    if not CHAIN_PATH.exists():
        return []
    records = []
    with CHAIN_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
    return records
