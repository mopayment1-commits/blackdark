"""Adaptive Decision Contract — extends decision_truth (spec §23, AIE-006)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.trust_dimensions import TrustDimensionVector


def build_adaptive_decision_contract(
    opportunity: dict[str, Any],
    *,
    symbol: str | None = None,
    router_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce full AIE Decision Contract from canonical decision_truth pipeline."""
    from decision_truth.pipeline import evaluate_opportunity

    dts = evaluate_opportunity(opportunity, symbol=symbol, record=False)
    trust = TrustDimensionVector.from_payload(opportunity)
    confidence_vector = {
        "evidence_coverage": opportunity.get("evidence_coverage") or "partial",
        "data_quality": opportunity.get("data_quality_score") or dts.uncertainty.get("data_quality"),
        "signal_agreement": "qualitative",
        "calibration_state": "uncalibrated",
        "regime_familiarity": opportunity.get("regime") or "unknown",
        "staleness": trust.freshness,
    }
    numeric_confidence = opportunity.get("numeric_confidence")
    if numeric_confidence is not None and not opportunity.get("calibration_evidence"):
        raise ValueError("numeric_confidence_requires_calibration_evidence")
    contract = {
        "current_stance": dts.decision_state.value,
        "decision_scope": {
            "symbol": dts.symbol,
            "horizon": dts.time_horizon,
            "asset_scope": symbol or dts.symbol,
        },
        "confidence_vector": confidence_vector,
        "numeric_confidence": numeric_confidence,
        "key_drivers": (dts.why or [])[:5],
        "contradictions": dts.why_not or [],
        "decision_boundary": {
            "type": "qualitative",
            "invalidation_condition": dts.invalidation_condition or "stale_or_regime_change",
        },
        "invalidation_conditions": [dts.invalidation_condition] if dts.invalidation_condition else [],
        "validity_window": opportunity.get("validity_window") or "until_stale",
        "next_check_trigger": opportunity.get("next_check") or "freshness_breach",
        "evidence_class": dts.evidence_class,
        "version_lineage": {
            "methodology_version": dts.methodology_version,
            "rule_version": opportunity.get("rule_version") or "router-v1",
        },
        "trust_dimensions": trust.to_dict(),
        "dts_contract": dts.to_dict(),
        "router": router_result or {},
    }
    return contract
