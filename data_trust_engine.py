"""
BLACKDARK — Data Trust Engine (quiet; under Oracle / heroes).

Every observation carries provenance. No source is infallible.
Aggregator/synthetic L2 cannot become Canonical Market State.
"""

from __future__ import annotations

from datetime import UTC, datetime
from statistics import median
from typing import Any, Literal

from data_source_trust import classify_source, classify_venue, l2_honesty_allowed

TrustAction = Literal["accept", "penalize", "quarantine", "reject", "not_applied"]

OBSERVATION_FIELDS: tuple[str, ...] = (
    "source",
    "source_class",
    "instrument",
    "venue",
    "event_time",
    "received_time",
    "latency_ms",
    "data_type",
    "raw_value",
    "normalized_value",
    "freshness",
    "quality_score",
    "confidence",
    "cross_source_agreement",
    "license_class",
    "redistribution_allowed",
    "book_origin",
    "decision_grade",
    "vintage",
)


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def make_observation(
    *,
    source: str,
    instrument: str,
    data_type: str,
    raw_value: Any,
    normalized_value: float | None = None,
    venue: str | None = None,
    event_time: str | None = None,
    received_time: str | None = None,
    latency_ms: float | None = None,
    book_origin: str | None = None,
    vintage: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Build a complete observation envelope (Data Trust Law §9)."""
    received = received_time or _utcnow_iso()
    class_row = classify_source(source, category=category)
    venue_id = (venue or source).strip().lower()
    venue_row = classify_venue(venue_id) if venue or data_type in {"l2", "ticker", "trade", "mid"} else {}
    origin = (book_origin or venue_row.get("book_origin") or "unknown").strip().lower()
    source_class = class_row.get("source_class")
    if data_type in {"l2", "ticker", "trade", "mid"} and venue_row.get("source_class"):
        source_class = venue_row.get("source_class")
    if data_type == "l2":
        decision_grade = l2_honesty_allowed(
            book_origin=origin,
            source_class=str(source_class or ""),
        )
    elif data_type in {"ticker", "trade", "mid"}:
        decision_grade = bool(
            venue_row.get("price_decision_grade")
            if venue_row
            else class_row.get("price_decision_grade")
        )
        if origin == "synthetic" and data_type != "mid":
            decision_grade = False
    else:
        decision_grade = class_row.get("decision_role") == "decision_grade"

    freshness = "unknown"
    if latency_ms is not None:
        if latency_ms <= 2000:
            freshness = "fresh"
        elif latency_ms <= 15000:
            freshness = "ok"
        else:
            freshness = "stale"

    quality = 0.0
    if decision_grade:
        quality += 40.0
    if source_class == "venue_direct":
        quality += 25.0
    elif source_class != "aggregator":
        quality += 10.0
    if freshness == "fresh":
        quality += 25.0
    elif freshness == "ok":
        quality += 15.0
    quality = round(min(100.0, quality), 1)
    reliability = source_reliability_score(
        freshness=freshness,
        directness=source_class == "venue_direct",
        latency_ms=latency_ms,
        completeness=100.0 if normalized_value is not None else 0.0,
    )

    return {
        "source": source,
        "source_class": source_class,
        "instrument": instrument.upper(),
        "venue": venue_id,
        "event_time": event_time,
        "received_time": received,
        "latency_ms": latency_ms,
        "data_type": data_type,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "freshness": freshness,
        "quality_score": quality,
        "source_reliability": reliability,
        "confidence": round(quality / 100.0, 4),
        "cross_source_agreement": None,
        "license_class": class_row.get("license_class"),
        "redistribution_allowed": bool(class_row.get("redistribution_allowed")),
        "book_origin": origin,
        "decision_grade": bool(decision_grade),
        "vintage": vintage,
        "truth_tier": class_row.get("truth_tier") or venue_row.get("truth_tier"),
    }


def source_reliability_score(
    *,
    freshness: str = "unknown",
    directness: bool = False,
    historical_accuracy: float = 50.0,
    cross_source_agreement: float | None = None,
    completeness: float = 50.0,
    latency_ms: float | None = None,
    anomaly_rate: float = 0.0,
) -> dict[str, Any]:
    """0–100 Source Reliability Score (Data Trust Law)."""
    fresh_pts = {"fresh": 20.0, "ok": 12.0, "stale": 0.0, "unknown": 6.0}.get(freshness, 6.0)
    direct_pts = 20.0 if directness else 6.0
    hist_pts = max(0.0, min(15.0, float(historical_accuracy) * 0.15))
    agree_pts = 15.0 if cross_source_agreement is None else max(0.0, min(15.0, float(cross_source_agreement) * 15.0))
    complete_pts = max(0.0, min(10.0, float(completeness) * 0.10))
    if latency_ms is None:
        lat_pts = 5.0
    elif latency_ms <= 500:
        lat_pts = 10.0
    elif latency_ms <= 2000:
        lat_pts = 7.0
    else:
        lat_pts = 2.0
    anomaly_pts = max(0.0, 10.0 - float(anomaly_rate) * 10.0)
    total = round(
        min(100.0, fresh_pts + direct_pts + hist_pts + agree_pts + complete_pts + lat_pts + anomaly_pts),
        1,
    )
    return {
        "score": total,
        "components": {
            "freshness": fresh_pts,
            "directness": direct_pts,
            "historical_accuracy": round(hist_pts, 1),
            "cross_source_agreement": round(agree_pts, 1),
            "completeness": round(complete_pts, 1),
            "latency": lat_pts,
            "anomaly_rate": round(anomaly_pts, 1),
        },
    }


def _rel_spread(values: list[float]) -> float:
    if not values:
        return 0.0
    lo, hi = min(values), max(values)
    mid = (hi + lo) / 2.0 if hi + lo else 0.0
    if mid <= 0:
        return 0.0
    return (hi - lo) / mid


def cross_source_consensus(
    observations: list[dict[str, Any]],
    *,
    max_rel_spread: float = 0.0025,
    outlier_rel: float = 0.0015,
) -> dict[str, Any]:
    """
    Build consensus from observations.

    A fails → use B. A and B disagree → quarantine. Stale → reject.
    Outlier → investigate. Single source → confidence penalty.
    """
    usable: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []

    for obs in observations:
        if obs.get("freshness") == "stale":
            rejected.append({**obs, "trust_reason": "stale"})
            continue
        if obs.get("data_type") == "l2" and not obs.get("decision_grade"):
            rejected.append({**obs, "trust_reason": "synthetic_or_aggregator_l2"})
            continue
        if obs.get("normalized_value") is None:
            rejected.append({**obs, "trust_reason": "missing_value"})
            continue
        usable.append(obs)

    grade = [o for o in usable if o.get("decision_grade")]
    pool = grade or []
    values = [float(o["normalized_value"]) for o in pool]
    action: TrustAction
    canonical: float | None = None
    penalty = 0.0
    agreement = 0.0

    if not pool:
        action = "reject"
        reason = "no_decision_grade_observations"
    elif len(pool) == 1:
        canonical = values[0]
        action = "penalize"
        penalty = 0.25
        agreement = 0.0
        reason = "single_source_only"
        pool[0]["cross_source_agreement"] = 0.0
    else:
        mid = float(median(values))
        inliers: list[dict[str, Any]] = []
        for obs, val in zip(pool, values):
            rel = abs(val - mid) / mid if mid else 0.0
            if rel > outlier_rel and _rel_spread(values) > max_rel_spread:
                quarantined.append({**obs, "trust_reason": "outlier"})
            else:
                inliers.append(obs)
        if len(inliers) < 2 and quarantined:
            action = "quarantine"
            reason = "cross_source_disagreement"
            canonical = mid
            agreement = 0.2
        else:
            kept_vals = [float(o["normalized_value"]) for o in (inliers or pool)]
            canonical = float(median(kept_vals))
            spread = _rel_spread(kept_vals)
            agreement = max(0.0, min(1.0, 1.0 - (spread / max_rel_spread)))
            if spread > max_rel_spread:
                action = "quarantine"
                reason = "spread_exceeds_tolerance"
            else:
                action = "accept"
                reason = "consensus"
            for obs in inliers or pool:
                obs["cross_source_agreement"] = round(agreement, 4)
        pool = inliers or pool

    return {
        "action": action,
        "reason": reason,
        "canonical_value": canonical,
        "confidence_penalty": penalty,
        "agreement": round(agreement, 4),
        "decision_grade_count": len(grade),
        "accepted": pool if action in {"accept", "penalize"} else [],
        "quarantined": quarantined,
        "rejected": rejected,
        "generated_at": _utcnow_iso(),
    }


def apply_data_trust_gate(
    score: float,
    *,
    observations: list[dict[str, Any]] | None = None,
    consensus: dict[str, Any] | None = None,
) -> tuple[float, dict[str, Any]]:
    """Fail-closed Oracle gate. Empty observations → not_applied (unit tests stay intact)."""
    meta: dict[str, Any] = {
        "applied": False,
        "veto": False,
        "abstain": False,
        "action": "not_applied",
        "reason": "no_observations",
        "confidence_penalty": 0.0,
    }
    if not observations and not consensus:
        return score, meta

    result = consensus or cross_source_consensus(list(observations or []))
    action = str(result.get("action") or "not_applied")
    penalty = float(result.get("confidence_penalty") or 0.0)
    adjusted = float(score)
    meta.update(
        {
            "applied": True,
            "action": action,
            "reason": result.get("reason"),
            "agreement": result.get("agreement"),
            "decision_grade_count": result.get("decision_grade_count"),
            "confidence_penalty": penalty,
            "canonical_value": result.get("canonical_value"),
        }
    )
    if action == "reject":
        meta["veto"] = True
        meta["abstain"] = True
        adjusted = min(adjusted, 49.0)
    elif action == "quarantine":
        meta["veto"] = True
        meta["abstain"] = True
        adjusted = min(adjusted, 49.0)
    elif action == "penalize":
        meta["abstain"] = True
        adjusted = min(adjusted, 59.0)
        adjusted *= 1.0 - penalty
    meta["message"] = (
        f"Data trust {action}: {result.get('reason')} "
        f"(decision_grade={result.get('decision_grade_count')})"
    )
    return round(max(0.0, adjusted), 4), meta
