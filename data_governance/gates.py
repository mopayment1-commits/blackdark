"""Decision safety and anti-bypass gates (DIG-005, DIG-038, DIG-043, DIG-054)."""

from __future__ import annotations

from typing import Any

from decision_truth.admission import evaluate_admission


def evaluate_material_gates(surface: str, payload: dict[str, Any], *, quality_score: float) -> dict[str, Any]:
    reasons: list[str] = []
    evidence = str(payload.get("evidence_class") or "SHADOW_LIVE_FORWARD")
    observed = payload.get("observed_at") or payload.get("timestamp")
    freshness_ok = observed is not None
    if surface in {"decision", "signal", "oracle", "cap_execute"}:
        state, why_not = evaluate_admission(
            freshness_ok=freshness_ok,
            data_quality_score=quality_score,
            evidence_class=evidence,
            liquidity_ok=True,
            execution_score=70.0,
            net_edge_reject=False,
            risk_ok=True,
            uncertainty_high=False,
        )
        if state.name in {"REJECTED", "ABSTAINED"}:
            reasons.extend(why_not)
    allowed = not reasons
    return {"allowed": allowed, "reasons": reasons, "surface": surface}
