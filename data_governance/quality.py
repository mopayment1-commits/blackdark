"""Quality gate — delegates to failure/quality with extended scoring."""

from __future__ import annotations

from typing import Any

from failure.quality import DataQualityState, classify_quality


def evaluate_quality(
    *,
    partial: bool = False,
    conflicting: bool = False,
    source_count: int = 1,
    provenance_score: float | None = None,
    historical_sufficient: bool = True,
) -> dict[str, Any]:
    q = classify_quality(partial=partial, conflicting=conflicting, source_count=source_count)
    completeness = 1.0 if not partial else 0.6
    timeliness = 0.9 if q.state not in {DataQualityState.SUSPECT} else 0.4
    consistency = 0.3 if conflicting else 0.95
    cross_agreement = min(1.0, source_count / 3.0)
    return {
        "quality_state": q.state.value,
        "completeness_score": round(completeness, 3),
        "timeliness_score": round(timeliness, 3),
        "consistency_score": round(consistency, 3),
        "cross_source_agreement": round(cross_agreement, 3),
        "provenance_status": "verified" if (provenance_score or 0) >= 55 else "insufficient",
        "historical_sufficiency": historical_sufficient,
    }


def attach_quality(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    conflicting = bool((out.get("dimension_conflict") or {}).get("veto"))
    partial = bool(out.get("partial_data"))
    source_count = int(out.get("source_count") or 1)
    prov = (out.get("data_provenance") or {}).get("total_score")
    hist = (out.get("historical_depth") or {}).get("sufficient", True)
    out["data_governance_quality"] = evaluate_quality(
        partial=partial,
        conflicting=conflicting,
        source_count=source_count,
        provenance_score=float(prov) if prov is not None else None,
        historical_sufficient=bool(hist),
    )
    out["data_quality_state"] = out["data_governance_quality"]["quality_state"]
    return out
