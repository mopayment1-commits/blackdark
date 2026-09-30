"""DTS-019 — Opportunity Rejection Engine from canonical govern records."""

from __future__ import annotations

from collections import Counter
from typing import Any

def record_govern_rejection(payload: dict[str, Any]) -> None:
    """Record reject/abstain/degrade into kill-rate board from govern path."""
    state = str(payload.get("decision_truth_state") or "")
    if state not in {"REJECTED", "ABSTAINED", "DEGRADED"}:
        return
    contract = ((payload.get("decision_truth") or {}).get("contract") or {})
    why_not = list(contract.get("why_not") or [])
    reason = why_not[0] if why_not else state.lower()
    try:
        from kill_rate_board import record_kill

        record_kill(
            "govern",
            reason,
            meta={
                "decision_id": payload.get("decision_id"),
                "symbol": payload.get("symbol"),
                "decision_truth_state": state,
                "why_not": why_not,
                "source": "canonical_govern_pipeline",
            },
        )
    except Exception:
        pass


def build_rejection_engine(payload: dict[str, Any]) -> dict[str, Any]:
    """Derive rejection metrics from govern stats + current decision."""
    from decision_truth.govern import govern_stats

    stats = govern_stats()
    contract = ((payload.get("decision_truth") or {}).get("contract") or {})
    admission = ((payload.get("decision_truth") or {}).get("admission") or {})
    why_not = list(contract.get("why_not") or admission.get("failed_gates") or [])
    state = str(payload.get("decision_truth_state") or contract.get("decision_state") or "UNAVAILABLE")

    categories = Counter()
    for code in why_not:
        categories[_categorize_reason(str(code))] += 1

    dg = payload.get("data_governance") or {}
    coverage = {
        "data_governance_state": dg.get("state") or payload.get("data_governance_state"),
        "freshness_available": bool((contract.get("freshness") or {}).get("state") == "AVAILABLE" or contract.get("freshness")),
        "evidence_class": contract.get("evidence_class"),
    }

    return {
        "methodology_version": "dts-p5-rejection-engine-1.0",
        "time_window": "session_cumulative",
        "total_evaluated": stats.get("evaluated", 0),
        "admitted": stats.get("admitted", 0),
        "degraded": stats.get("degraded", 0),
        "abstained": stats.get("abstained", 0),
        "rejected": stats.get("rejected", 0),
        "unavailable": stats.get("unavailable", 0),
        "current_decision_state": state,
        "rejection_reason_categories": dict(categories),
        "dominant_rejection_causes": [c for c, _ in categories.most_common(5)],
        "current_why_not": why_not,
        "data_coverage": coverage,
        "derived_from": "canonical_govern_pipeline",
        "fabricated_metrics": False,
    }


def _categorize_reason(code: str) -> str:
    lowered = code.lower()
    if "fresh" in lowered or "stale" in lowered:
        return "freshness"
    if "exec" in lowered or "liquidity" in lowered or "fill" in lowered:
        return "execution"
    if "net_edge" in lowered or "cost" in lowered or "economic" in lowered:
        return "economic"
    if "risk" in lowered or "portfolio" in lowered or "stress" in lowered:
        return "risk"
    if "evidence" in lowered or "grade" in lowered or "calibration" in lowered:
        return "evidence"
    if "conflict" in lowered or "quality" in lowered:
        return "data_quality"
    if "uncertain" in lowered:
        return "uncertainty"
    return "other"
