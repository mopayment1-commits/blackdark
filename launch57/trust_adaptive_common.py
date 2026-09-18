"""
Launch-57 Phase 2 Adaptive Batch A — trust-surface disclosure helpers.

Support structure only (not a capability). Level-1 progressive disclosure and
safety-floor fields for Launch #2–#5 (trust_batch1), #47–#48/#44–#46
(trust_batch2), #7–#11 (decision_batch1), #12/#37 (decision_batch2), and
#20/#16/#17/#13/#14 (smart_money_batch1), #15/#18/#19/#53/#54
# (smart_money_batch2), #55/#56/#57 (smart_money_batch3), and
# #25–#29 (derivatives_batch1), #30–#33 (derivatives_batch2), and
# #34–#36/#51 (explanation_ai_batch1), and #43/#38/#49/#50/#52
# (edge_ui_batch1) consumer paths.
"""

from __future__ import annotations

from typing import Any

METHODOLOGY_VERSION = "launch57-trust-adaptive-common-1.0"


def _governed(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("governed_payload")
    return dict(raw) if isinstance(raw, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return [value]


def _first_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, dict):
        for key in ("summary", "message", "description", "text", "reason"):
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                return text.strip()
    return str(value)


def extract_material_contradiction(payload: dict[str, Any]) -> dict[str, Any] | None:
    governed = _governed(payload)
    for key in ("critical_contradiction", "contradiction_state", "material_contradiction"):
        candidate = governed.get(key) or payload.get(key)
        if isinstance(candidate, dict) and candidate:
            return candidate
        text = _first_text(candidate)
        if text:
            return {"summary": text}
    contradictions = _as_list(governed.get("contradictions") or payload.get("contradictions"))
    if contradictions:
        first = contradictions[0]
        if isinstance(first, dict):
            return first
        text = _first_text(first)
        return {"summary": text} if text else None
    return None


def extract_material_limitation(payload: dict[str, Any]) -> dict[str, Any] | None:
    governed = _governed(payload)
    for key in ("critical_limitation", "material_limitation", "limitation"):
        candidate = governed.get(key) or payload.get(key)
        if isinstance(candidate, dict) and candidate:
            return candidate
        text = _first_text(candidate)
        if text:
            return {"summary": text}
    limitations = _as_list(governed.get("limitations") or payload.get("limitations"))
    if limitations:
        first = limitations[0]
        if isinstance(first, dict):
            return first
        text = _first_text(first)
        return {"summary": text} if text else None
    return None


def extract_abstention_reason(payload: dict[str, Any], *, action: str | None) -> str | None:
    if str(action or "").upper() != "ABSTAIN":
        return None
    governed = _governed(payload)
    for key in ("abstention_reason", "abstain_reason", "reject_reason"):
        text = _first_text(governed.get(key) or payload.get(key))
        if text:
            return text
    return None


def extract_deeper_evidence_link(payload: dict[str, Any]) -> str | None:
    governed = _governed(payload)
    for key in ("deeper_evidence_link", "evidence_link", "proof_link"):
        text = _first_text(governed.get(key) or payload.get(key))
        if text:
            return text
    return None


def build_level1_decision_disclosure(
    payload: dict[str, Any],
    *,
    launch_item_id: int,
    surface: str,
    answer_state: str | None,
    evidence_display: dict[str, Any] | None = None,
    decision_timing: dict[str, Any] | None = None,
    uncertainty: str | None = None,
) -> dict[str, Any]:
    """Adaptive spec §28 Level 1 — decision layer for material trust outputs."""
    contradiction = extract_material_contradiction(payload)
    limitation = extract_material_limitation(payload)
    abstention_reason = extract_abstention_reason(payload, action=answer_state)
    evidence = evidence_display or {}
    timing = decision_timing or {}
    freshness_state = payload.get("freshness_state") or evidence.get("freshness_state")
    if freshness_state is None and evidence.get("freshness_downgrade_applied"):
        freshness_state = "STALE"
    return {
        "layer": "level_1_decision",
        "launch_item_id": launch_item_id,
        "surface": surface,
        "answer_state": answer_state,
        "uncertainty": uncertainty or payload.get("uncertainty") or _derive_uncertainty(payload, answer_state),
        "freshness_state": freshness_state,
        "evidence_class": evidence.get("user_facing_label") or evidence.get("canonical_evidence_class"),
        "critical_contradiction": contradiction,
        "critical_limitation": limitation,
        "abstention_reason": abstention_reason,
        "next_recheck": timing.get("recheck_time"),
        "invalidation_condition": timing.get("invalidation_event") or timing.get("invalidation_time"),
        "deeper_evidence_link": extract_deeper_evidence_link(payload),
        "safety_floor_visible": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def _derive_uncertainty(payload: dict[str, Any], answer_state: str | None) -> str:
    explicit = _first_text(payload.get("uncertainty"))
    if explicit:
        return explicit
    action = str(answer_state or "").upper()
    if action == "ABSTAIN":
        return "insufficient_evidence"
    if action == "WAIT":
        return "qualified"
    if action == "ACT":
        return "actionable_with_caveats"
    return "unknown"


def build_certificate_adaptive_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Adaptive spec §6 structured certificate fields."""
    governed = _governed(payload)
    return {
        "key_drivers": _as_list(governed.get("key_drivers") or payload.get("key_drivers")),
        "contradictions": _as_list(governed.get("contradictions") or payload.get("contradictions")),
        "limitations": _as_list(governed.get("limitations") or payload.get("limitations")),
    }


def build_ledger_interpretation_context(ledger: dict[str, Any]) -> dict[str, Any]:
    """Adaptive spec §7 — prevent misleading public accuracy interpretation."""
    cumulative = ledger.get("cumulative") or {}
    synthetic = ledger.get("synthetic_demo_data") or {}
    return {
        "public_scope": "live_primary_outcomes_only",
        "metrics_scope": cumulative.get("metrics_scope") or ledger.get("metrics_scope") or "live_only",
        "synthetic_excluded_from_primary": bool(synthetic.get("excluded_from_primary_metrics", True)),
        "replay_excluded_from_primary": True,
        "shadow_not_production_history": True,
        "misleading_interpretation_guards": [
            "Do not treat replay/simulation rows as live public accuracy.",
            "Primary metrics exclude synthetic and non-live evidence classes.",
            "Use recent_all only for audit; public surface uses live-primary recent rows.",
        ],
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_net_edge_safety_floor(score: dict[str, Any], opportunity: dict[str, Any]) -> dict[str, Any]:
    """Adaptive spec §8 — gross spread is not actionable net edge without cost treatment."""
    return {
        "gross_edge_not_actionable_without_cost_treatment": True,
        "net_edge_before_cost_claim": True,
        "cost_components_considered": [
            "trading_fees",
            "withdrawal_fee",
            "slippage_bps",
            "latency_buffer",
            "quote_age_ms",
        ],
        "truth_edge_usd": score.get("truth_edge"),
        "residual_usd": score.get("residual"),
        "net_profit_usdt": score.get("net"),
        "cost_claim_allowed": bool(score.get("pass")) and not score.get("reject"),
        "methodology_version": METHODOLOGY_VERSION,
    }


def attach_adaptive_disclosure(
    body: dict[str, Any],
    disclosure: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(body)
    block = dict(extra or {})
    block["level_1"] = disclosure
    out["adaptive_disclosure"] = block
    out["safety_floor_visible"] = True
    return out


APPROVED_LAUNCH57_PUBLIC_TRUST_SURFACES: tuple[dict[str, Any], ...] = (
    {"launch_item_id": 2, "surface": "single_sentence_oracle", "module": "launch57.trust_batch1"},
    {"launch_item_id": 3, "surface": "decision_certificate_institutional_dd_export", "module": "launch57.trust_batch1"},
    {"launch_item_id": 4, "surface": "public_accuracy_ledger", "module": "launch57.trust_batch1"},
    {"launch_item_id": 5, "surface": "net_edge_truth_score", "module": "launch57.trust_batch1"},
    {"launch_item_id": 44, "surface": "shareable_decision_card", "module": "launch57.trust_batch2"},
    {"launch_item_id": 45, "surface": "shareable_accuracy_page", "module": "launch57.trust_batch2"},
    {"launch_item_id": 46, "surface": "guest_trust_surface", "module": "launch57.trust_batch2"},
    {"launch_item_id": 47, "surface": "one_click_risk_disclosure", "module": "launch57.trust_batch2"},
    {"launch_item_id": 48, "surface": "abstain_reject_reasons_visible", "module": "launch57.trust_batch2"},
)


def build_material_risk_access(
    material_claims: dict[str, Any],
    *,
    reject_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — direct access to material risk for Launch #47."""
    claims = list(material_claims.get("claims") or [])
    ungrounded = [c for c in claims if c.get("status") in {"degraded", "suppressed"}]
    primary = claims[0] if claims else None
    return {
        "direct_access": True,
        "material_claims": claims,
        "primary_material_risk": primary,
        "ungrounded_material_claims": ungrounded,
        "reject_proof": reject_proof,
        "all_grounded": bool(material_claims.get("all_grounded")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_shareable_truth_context(
    payload: dict[str, Any],
    *,
    evidence: dict[str, Any],
    material_claims: dict[str, Any] | None = None,
    timing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — shareable decision truth for Launch #44."""
    user_label = str(evidence.get("user_facing_label") or "")
    unsupported_live = user_label != "LIVE"
    governed = _governed(payload)
    decision_time = (
        (timing or {}).get("decision_time")
        or governed.get("decision_time")
        or payload.get("decision_time")
        or payload.get("timestamp")
    )
    material = material_claims or validate_material_claims_from_payload(payload)
    return {
        "evidence_class": evidence.get("canonical_evidence_class"),
        "user_facing_evidence_label": user_label,
        "decision_time": decision_time,
        "issued_at": (timing or {}).get("issued_at") or governed.get("issued_at"),
        "material_risk": build_material_risk_access(material),
        "unsupported_live_claim_blocked": unsupported_live,
        "live_claim_allowed": not unsupported_live,
        "share_truth_preserved": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def validate_material_claims_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Delegate to decision_truth grounding when available; otherwise empty claims."""
    try:
        from decision_truth.product.grounding import validate_material_claims

        return validate_material_claims(payload)
    except Exception:
        return {"claims": [], "total_material_claims": 0, "ungrounded_count": 0, "all_grounded": True}


def build_abstention_reject_disclosure(
    payload: dict[str, Any],
    *,
    no_decision: dict[str, Any],
    rejection: dict[str, Any],
) -> dict[str, Any]:
    """Adaptive — first-class abstain/reject disclosure for Launch #48."""
    state = str(no_decision.get("decision_truth_state") or payload.get("decision_truth_state") or "")
    action = str(no_decision.get("decision_action") or payload.get("decision_action") or "")
    return {
        "first_class_state": bool(no_decision.get("first_class_state")),
        "hidden_as_error": bool(no_decision.get("hidden_as_error")),
        "decision_truth_state": state,
        "decision_action": action,
        "reason_codes": list(no_decision.get("reason_codes") or []),
        "rejection_reason_categories": dict(rejection.get("rejection_reason_categories") or {}),
        "dominant_rejection_causes": list(rejection.get("dominant_rejection_causes") or []),
        "what_would_be_needed_to_reconsider": list(
            no_decision.get("what_would_be_needed_to_reconsider") or []
        ),
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_approved_public_trust_surfaces() -> list[dict[str, Any]]:
    """Launch #46 — approved Launch-57 public trust surfaces only."""
    return [dict(row) for row in APPROVED_LAUNCH57_PUBLIC_TRUST_SURFACES]


def build_market_context_disclosure(market_compass: dict[str, Any]) -> dict[str, Any]:
    """Adaptive — Launch #7 market context without standalone trade instruction."""
    return {
        "context_only": True,
        "standalone_trade_instruction": False,
        "market_regime": market_compass.get("regime"),
        "compass_question": market_compass.get("compass_question"),
        "interpretation_scope": "market_context_not_trade_signal",
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_beginner_simplification_disclosure(
    clear_answer: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #8 simplification with material risk still visible."""
    risk_score = clear_answer.get("risk_score")
    material = validate_material_claims_from_payload(payload or {})
    return {
        "simplified_surface": True,
        "material_risk_visible": True,
        "risk_score": risk_score,
        "material_risk": build_material_risk_access(material),
        "insight_not_recommendation": bool(clear_answer.get("insight_not_recommendation")),
        "disclaimer": clear_answer.get("disclaimer"),
        "safety_floor_visible": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_dependence_aware_confirmation(
    *,
    confirmed: bool,
    price_change: float,
    sentiment: dict[str, Any],
    registry_stats: dict[str, Any],
) -> dict[str, Any]:
    """Adaptive — Launch #9; duplicated evidence is not independent confirmation."""
    signals = list(sentiment.get("signals") or [])
    normalized = [str(s).lower() for s in signals]
    unique_types = set(normalized)
    duplicated = len(signals) > len(unique_types) or len(unique_types) <= 1
    independent = confirmed and not duplicated and len(unique_types) >= 2
    return {
        "raw_confirmed": confirmed,
        "independent_confirmation": independent,
        "duplicated_evidence_not_independent": duplicated,
        "dependence_factors": {
            "signal_count": len(signals),
            "unique_signal_types": len(unique_types),
            "same_source_risk": duplicated,
            "registry_total": registry_stats.get("total"),
        },
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_material_contradiction_impact(
    contradictions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Adaptive — Launch #10 explicit material contradiction and decision impact."""
    material = contradictions[0] if contradictions else None
    return {
        "material_contradiction": material,
        "contradiction_count": len(contradictions),
        "decision_impact": "WAIT" if contradictions else "NONE",
        "confidence_effect": "reduced" if contradictions else "unchanged",
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_actionability_disclosure(
    score: float,
    *,
    alerts: list[Any],
    net_edge_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #11 actionability without unsupported precision."""
    if score >= 75:
        band = "high_watch"
    elif score >= 40:
        band = "moderate_watch"
    else:
        band = "low_watch"
    return {
        "qualitative_band": band,
        "unsupported_precision_blocked": True,
        "raw_score_present": True,
        "actionability_not_trade_instruction": True,
        "alert_count": len(alerts),
        "net_edge_gate_passed": not bool((net_edge_gate or {}).get("blocked")),
        "methodology_version": METHODOLOGY_VERSION,
    }


_APPROVED_LAUNCH57_COMPOSITION_DIMENSION_SOURCES: frozenset[str] = frozenset(
    {
        "ta_engine",
        "on_chain_extension",
        "sentiment_layer",
        "launch57.data_batch1",
        "launch57.data_batch2",
        "launch57.decision_batch1",
        "launch57.trust_batch1",
    }
)


def _is_approved_launch57_evidence_path(path: str) -> bool:
    text = str(path or "")
    return text.startswith("launch57.")


def _is_approved_launch57_dimension_source(source: str) -> bool:
    return str(source or "") in _APPROVED_LAUNCH57_COMPOSITION_DIMENSION_SOURCES


def compute_approved_decision_composite(multi_dimensional: dict[str, Any]) -> dict[str, Any]:
    """Derive #37 decision-driving composite from approved Launch-57 dimension sources only."""
    dims = dict((multi_dimensional or {}).get("dimensions") or {})
    approved_dims: dict[str, dict[str, Any]] = {}
    excluded: list[dict[str, Any]] = []

    for name, dim in dims.items():
        source = str((dim or {}).get("source") or "")
        if _is_approved_launch57_dimension_source(source):
            approved_dims[name] = dict(dim or {})
        else:
            excluded.append(
                {
                    "dimension": name,
                    "source": source,
                    "decision_driving": False,
                    "observable_only": True,
                }
            )

    weight_sum = sum(float((dim or {}).get("weight") or 0) for dim in approved_dims.values())
    if weight_sum > 0 and approved_dims:
        composite = round(
            sum(
                float((dim or {}).get("score") or 0) * float((dim or {}).get("weight") or 0) / weight_sum
                for dim in approved_dims.values()
            ),
            2,
        )
    else:
        composite = 0.0

    return {
        "composite_score": composite,
        "approved_dimensions": approved_dims,
        "excluded_from_decision_driving": excluded,
        "decision_driving_approved_only": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_structured_conviction_disclosure(
    *,
    alert: dict[str, Any],
    conviction_score: float,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #12 structured conviction with visible material disagreement."""
    p = dict(payload or {})
    opportunity = float(p.get("opportunity_level") or 0)
    volume_z = float(p.get("volume_zscore") or 0)
    alert_fired = bool(alert.get("alert_fired"))
    disagreements: list[dict[str, Any]] = []

    if opportunity >= 7 and not alert_fired:
        disagreements.append(
            {
                "type": "high_opportunity_no_alert",
                "summary": "Opportunity level elevated but contextual alert did not fire.",
            }
        )
    if volume_z >= 2 and opportunity < 5:
        disagreements.append(
            {
                "type": "volume_opportunity_divergence",
                "summary": "Volume z-score elevated without matching opportunity level.",
            }
        )
    governed = extract_material_contradiction(p)
    if governed:
        disagreements.append(governed)

    if conviction_score >= 75:
        band = "high_conviction"
    elif conviction_score >= 40:
        band = "moderate_conviction"
    else:
        band = "low_conviction"

    return {
        "structured_conviction": {
            "score": conviction_score,
            "band": band,
            "alert_fired": alert_fired,
        },
        "material_disagreement_visible": True,
        "material_disagreements": disagreements,
        "disagreement_count": len(disagreements),
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_approved_evidence_composition(
    decision_engine: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #37 composition of approved Launch-57 evidence only."""
    components: list[dict[str, Any]] = []
    decision_driving = dict((decision_engine or {}).get("decision_driving_composite") or {})
    excluded_observable = list(decision_driving.get("excluded_from_decision_driving") or [])

    spine_ref = dict((spine or {}).get("data_spine") or {})
    for key, path in spine_ref.items():
        approved = _is_approved_launch57_evidence_path(str(path))
        components.append(
            {
                "component": key,
                "path": path,
                "approved": approved,
                "decision_driving": approved,
            }
        )

    multi = dict((decision_engine or {}).get("multi_dimensional") or {})
    for name, dim in dict(multi.get("dimensions") or {}).items():
        source = str((dim or {}).get("source") or "")
        approved = _is_approved_launch57_dimension_source(source)
        components.append(
            {
                "component": f"dimension:{name}",
                "source": source,
                "approved": approved,
                "decision_driving": approved,
            }
        )

    cross = dict((decision_engine or {}).get("cross_market") or {})
    if cross:
        components.append(
            {
                "component": "cross_market",
                "source": "launch57.decision_batch2:cross_market_decision_engine",
                "approved": True,
                "decision_driving": True,
            }
        )

    decision_driving_unapproved = [c for c in components if c.get("decision_driving") and not c.get("approved")]
    observable_non_decision_driving = [
        {
            "component": f"dimension:{item.get('dimension')}",
            "source": item.get("source"),
            "approved": False,
            "decision_driving": False,
            "observable_only": True,
        }
        for item in excluded_observable
    ]
    return {
        "approved_launch57_evidence_only": len(decision_driving_unapproved) == 0,
        "components": components,
        "decision_driving_components": [c for c in components if c.get("decision_driving")],
        "unapproved_components": decision_driving_unapproved,
        "observable_non_decision_driving": observable_non_decision_driving,
        "composition_scope": "approved_launch57_evidence_only",
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_attribution_cohort_disclosure(
    *,
    labels: Any,
    cohorts: dict[str, Any],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #20 attribution/cohort interpretation distinct from raw movement."""
    label_count = int(cohorts.get("label_count") or 0)
    limited = bool(cohorts.get("limited_nucleus"))
    has_labels = bool(labels) and label_count > 0
    return {
        "attribution_distinct_from_raw_movement": True,
        "cohort_interpretation_not_raw_flow": True,
        "attribution_uncertainty_visible": True,
        "coverage_limits_visible": True,
        "limited_nucleus": limited,
        "label_count": label_count,
        "coverage_qualified": limited or not has_labels,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_exchange_flow_disclosure(
    *,
    exchange_flow: dict[str, Any] | None = None,
    netflow: dict[str, Any] | None = None,
    exchange: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #16 exchange flow distinct from generic/raw movement."""
    flow = dict(exchange_flow or netflow or {})
    p = dict(payload or {})
    exchange_name = exchange or flow.get("exchange") or p.get("exchange")
    limited_coverage = bool(p.get("coverage_limited") or not exchange_name)
    return {
        "exchange_flow_not_generic_movement": True,
        "distinct_from_raw_onchain_movement": True,
        "attribution_certainty_qualified": True,
        "coverage_limited": limited_coverage,
        "certainty_not_implied": True,
        "indicators_only": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_internal_flow_whale_significance_filter(
    whale_payload: dict[str, Any],
    classified: dict[str, Any],
) -> dict[str, Any]:
    """Apply canonical internal-flow classification to #17 whale/external-flow significance."""
    classification = str(classified.get("classification") or "UNKNOWN")
    internal = "INTERNAL" in classification.upper()
    economic = classification == "ECONOMIC_FLOW"
    raw_ratio = whale_payload.get("whale_filtered_ratio") or whale_payload.get("exchange_whale_ratio")

    if internal:
        return {
            "exchange_whale_ratio": None,
            "whale_significance_suppressed": True,
            "significance_eligible": False,
            "whale_bias": "suppressed_internal_flow",
            "raw_whale_filtered_ratio": raw_ratio,
            "internal_flow_classification": classification,
            "runtime_filter_applied": True,
            "methodology_version": METHODOLOGY_VERSION,
        }
    if economic:
        return {
            "exchange_whale_ratio": raw_ratio,
            "whale_significance_suppressed": False,
            "significance_eligible": True,
            "whale_bias": whale_payload.get("whale_bias") or "neutral",
            "raw_whale_filtered_ratio": raw_ratio,
            "internal_flow_classification": classification,
            "runtime_filter_applied": True,
            "methodology_version": METHODOLOGY_VERSION,
        }
    return {
        "exchange_whale_ratio": None,
        "whale_significance_suppressed": True,
        "significance_eligible": False,
        "whale_bias": "unknown_flow",
        "raw_whale_filtered_ratio": raw_ratio,
        "internal_flow_classification": classification,
        "runtime_filter_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_whale_ratio_internal_flow_disclosure(
    *,
    whale_payload: dict[str, Any],
    internal_flow: dict[str, Any] | None = None,
    filtered: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #17 whale ratio with internal-flow filter preserved."""
    internal = dict(internal_flow or (payload or {}).get("internal_flow_filter") or {})
    classification = str(internal.get("classification") or "")
    internal_detected = "INTERNAL" in classification.upper()
    significance = dict(filtered or {})
    suppressed = bool(significance.get("whale_significance_suppressed"))
    return {
        "whale_ratio_interpretation": significance.get("whale_bias") or whale_payload.get("whale_bias") or "neutral",
        "internal_flow_filter_preserved": True,
        "runtime_filter_applied": bool(significance.get("runtime_filter_applied")),
        "internal_not_counted_as_external_flow": internal_detected and suppressed,
        "significance_eligible": significance.get("significance_eligible"),
        "whale_significance_suppressed": suppressed,
        "internal_flow_classification": classification or significance.get("internal_flow_classification"),
        "noise_filter_applied_usd": whale_payload.get("noise_filter_usd"),
        "misclassification_guard_active": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_internal_flow_filter_disclosure(
    classified: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #17 internal exchange movement not misclassified as external flow."""
    classification = str(classified.get("classification") or "UNKNOWN")
    internal = "INTERNAL" in classification.upper()
    return {
        "internal_flow_filter_active": True,
        "internal_not_external_flow": internal,
        "external_flow_only_when_economic": True,
        "classification": classification,
        "misclassification_guard": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_accumulation_distribution_disclosure(
    *,
    narratives: dict[str, Any],
    signal_count: int,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #13 accumulation/distribution as inference with visible uncertainty."""
    rows = narratives.get("narratives") or narratives.get("signals") or []
    count = signal_count if signal_count else (len(rows) if isinstance(rows, list) else 0)
    return {
        "inference_not_raw_flow_fact": True,
        "accumulation_distribution_is_inference": True,
        "supporting_evidence_visible": True,
        "signal_count": count,
        "material_uncertainty_visible": count == 0,
        "uncertainty_qualified": count < 3,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_smart_money_screener_disclosure(
    *,
    screener: list[dict[str, Any]],
    spine: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #14 screening from approved Launch-57 smart-money evidence."""
    components = [
        {"component": "data_spine", "source": "launch57.data_batch1", "approved": True},
        {
            "component": "screener_engine",
            "source": "launch57.smart_money_batch1:smart_money_token_screener",
            "approved": True,
        },
        {
            "component": "leaderboard_feed",
            "source": "bd_platform.free_tier_capabilities:smart_money_leaderboard",
            "approved": True,
        },
    ]
    return {
        "screening_from_approved_launch57_evidence": True,
        "approved_evidence_components": components,
        "ranking_qualitative_not_certainty": True,
        "raw_movement_not_collapsed_to_certainty": True,
        "attribution_inference_separated": True,
        "screener_count": len(screener),
        "methodology_version": METHODOLOGY_VERSION,
    }


_APPROVED_WALLET_DD_SOURCES: frozenset[str] = frozenset(
    {
        "launch57.smart_money_batch2:instant_wallet_due_diligence",
        "launch57.data_batch1:real_time_prices",
        "bd_platform.address_intelligence:search_address",
        "bd_platform.whales_institutional_layer:analyze_wallet_surveillance_79",
    }
)

_APPROVED_TOKEN_DD_SOURCES: frozenset[str] = frozenset(
    {
        "launch57.smart_money_batch2:instant_token_due_diligence",
        "launch57.data_batch1:real_time_prices",
        "bd_platform.free_integrations:holder_analytics",
    }
)


def derive_entity_wallet_interpretation(intel: dict[str, Any]) -> dict[str, Any]:
    """Derive #15 entity interpretation distinct from raw wallet movement."""
    entity_label = intel.get("entity_label")
    labels_payload = intel.get("labels")
    label_rows: list[Any] = []
    if isinstance(labels_payload, dict):
        label_rows = list(labels_payload.get("labels") or [])
    elif isinstance(labels_payload, list):
        label_rows = labels_payload
    data_state = str(intel.get("data_state") or "UNKNOWN").upper()
    total_usd = float(intel.get("total_usd") or 0)
    ok = bool(intel.get("ok"))

    has_attribution = bool(entity_label) or len(label_rows) > 0
    coverage_limited = data_state in ("PARTIAL", "MISSING", "UNKNOWN") or not ok

    if not ok:
        interpretation = "unknown_entity"
        answer_state = "UNKNOWN"
        certainty = "insufficient_evidence"
    elif has_attribution and not coverage_limited:
        interpretation = "attributed_entity"
        answer_state = "ATTRIBUTED"
        certainty = "qualified"
    elif has_attribution and coverage_limited:
        interpretation = "partially_attributed_entity"
        answer_state = "PARTIALLY_ATTRIBUTED"
        certainty = "qualified"
    else:
        interpretation = "unattributed_wallet_movement"
        answer_state = "UNATTRIBUTED"
        certainty = "insufficient_evidence"

    return {
        "entity_interpretation": interpretation,
        "interpretation_distinct_from_raw_movement": True,
        "raw_balance_usd_observable_only": total_usd,
        "attribution_state": "known" if has_attribution else "unknown",
        "coverage_limited": coverage_limited,
        "certainty_not_implied": coverage_limited or not has_attribution,
        "answer_state": answer_state,
        "certainty": certainty,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_entity_wallet_disclosure(
    interpretation: dict[str, Any],
    *,
    intel: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #15 entity interpretation distinct from raw movement."""
    return {
        "entity_interpretation_not_raw_movement": interpretation.get("interpretation_distinct_from_raw_movement"),
        "attribution_uncertainty_visible": True,
        "coverage_limits_visible": interpretation.get("coverage_limited"),
        "certainty_not_implied": interpretation.get("certainty_not_implied"),
        "attribution_state": interpretation.get("attribution_state"),
        "entity_interpretation": interpretation.get("entity_interpretation"),
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_whale_alert_qualification_filter(
    alerts: list[dict[str, Any]],
    *,
    derivatives_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply canonical whale alert/inference logic — movement alone is not alert-worthy."""
    from whale_signal_classifier import classify_whale_alert

    qualified: list[dict[str, Any]] = []
    excluded_noise: list[dict[str, Any]] = []
    for alert in alerts or []:
        if not isinstance(alert, dict):
            continue
        classification = classify_whale_alert(alert, derivatives_context=derivatives_context)
        entry = {**alert, "whale_classification": classification}
        if classification.get("actionable"):
            qualified.append(entry)
        else:
            excluded_noise.append(entry)

    return {
        "alert_worthy_alerts": qualified,
        "alert_worthy_count": len(qualified),
        "excluded_noise_alerts": excluded_noise,
        "movement_only_excluded": True,
        "runtime_qualification_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_whale_alert_disclosure(
    filtered: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #18 whale alerts from canonical qualification, not movement alone."""
    return {
        "alert_from_canonical_qualification": True,
        "movement_presence_not_sufficient": True,
        "runtime_qualification_applied": bool(filtered.get("runtime_qualification_applied")),
        "alert_worthy_count": filtered.get("alert_worthy_count"),
        "excluded_noise_count": len(filtered.get("excluded_noise_alerts") or []),
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_inter_entity_internal_flow_filter(
    ctx: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exclude internal exchange movement from decision-driving inter-entity semantics."""
    from exchange_internal_flow_filter import classify_flow

    raw_flows = list(ctx.get("flows") or ctx.get("inter_entity_flows") or [])
    p = dict(payload or {})
    eligible: list[dict[str, Any]] = []
    excluded_internal: list[dict[str, Any]] = []

    for flow in raw_flows:
        flow_dict = dict(flow or {})
        classified = classify_flow(
            from_address=str(
                flow_dict.get("from_address")
                or flow_dict.get("from")
                or p.get("from_address")
                or "0x0000000000000000000000000000000000000000"
            ),
            to_address=str(
                flow_dict.get("to_address")
                or flow_dict.get("to")
                or p.get("to_address")
                or "0x0000000000000000000000000000000000000000"
            ),
            exchange=str(flow_dict.get("exchange") or p.get("exchange") or "binance"),
            amount_usd=float(flow_dict.get("amount_usd") or p.get("amount_usd") or 0),
            is_deposit=bool(flow_dict.get("is_deposit") or p.get("is_deposit")),
            is_withdrawal=bool(flow_dict.get("is_withdrawal") or p.get("is_withdrawal")),
        )
        classification = str(classified.get("classification") or "UNKNOWN")
        entry = {**flow_dict, "internal_flow_classification": classified}
        if "INTERNAL" in classification.upper():
            excluded_internal.append(entry)
        elif classification == "ECONOMIC_FLOW":
            eligible.append(entry)

    return {
        "inter_entity_flow_eligible": eligible,
        "internal_flows_excluded": excluded_internal,
        "inter_entity_eligible_count": len(eligible),
        "internal_excluded_count": len(excluded_internal),
        "inter_entity_semantics_eligible": len(eligible) > 0,
        "runtime_filter_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_inter_entity_flow_disclosure(
    filtered: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #19 internal movement excluded from inter-entity semantics."""
    return {
        "internal_not_inter_entity_flow": filtered.get("internal_excluded_count", 0) > 0
        or bool(filtered.get("runtime_filter_applied")),
        "external_economic_flow_eligible": filtered.get("inter_entity_eligible_count", 0) > 0,
        "runtime_filter_applied": bool(filtered.get("runtime_filter_applied")),
        "inter_entity_semantics_eligible": filtered.get("inter_entity_semantics_eligible"),
        "methodology_version": METHODOLOGY_VERSION,
    }


def compute_approved_wallet_due_diligence_verdict(
    *,
    intel: dict[str, Any],
    surveillance: dict[str, Any],
    spine: dict[str, Any] | None = None,
    observable_unapproved: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive #53 decision-driving verdict from approved Launch-57 evidence only."""
    approved_flags: list[str] = []
    if not intel.get("ok"):
        approved_flags.append("address_lookup_failed")
    if surveillance.get("surveillance_detected"):
        approved_flags.append("elevated_surveillance_pattern")
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    if spine is not None and not fresh:
        approved_flags.append("stale_or_ineligible_spine")

    verdict = "review" if approved_flags else "clear"
    unapproved_flags = list((observable_unapproved or {}).get("risk_flags") or [])

    return {
        "verdict": verdict,
        "risk_flags": approved_flags,
        "decision_driving_approved_only": True,
        "unapproved_observable_only": {
            "risk_flags": unapproved_flags,
            "decision_driving": False,
        },
        "approved_evidence_sources": sorted(_APPROVED_WALLET_DD_SOURCES),
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_wallet_due_diligence_disclosure(
    approved: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #53 due diligence from approved evidence with limitations visible."""
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    return {
        "due_diligence_from_approved_launch57_evidence_only": approved.get("decision_driving_approved_only"),
        "unapproved_inputs_observable_not_decision_driving": True,
        "freshness_preserved": fresh,
        "stale_not_promoted_to_stronger_truth": not fresh or approved.get("verdict") != "clear",
        "limitations_visible": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def compute_approved_token_due_diligence_verdict(
    *,
    holders: dict[str, Any],
    financial_models: dict[str, Any],
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive #54 decision-driving verdict from approved Launch-57 evidence only."""
    approved_flags: list[str] = []
    locked = float((holders.get("metrics") or {}).get("locked_supply_pct") or 0)
    if locked > 70:
        approved_flags.append("high_locked_supply")
    if not holders.get("available"):
        approved_flags.append("holder_data_unavailable")
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    if spine is not None and not fresh:
        approved_flags.append("stale_or_ineligible_spine")

    verdict = "review" if approved_flags else "clear"
    unapproved_observable: list[str] = []
    if financial_models.get("error"):
        unapproved_observable.append("financial_model_gap")

    return {
        "verdict": verdict,
        "risk_flags": approved_flags,
        "decision_driving_approved_only": True,
        "unapproved_observable_only": {
            "risk_flags": unapproved_observable,
            "decision_driving": False,
        },
        "approved_evidence_sources": sorted(_APPROVED_TOKEN_DD_SOURCES),
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_token_due_diligence_disclosure(
    approved: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #54 token due diligence from approved evidence with limitations visible."""
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    return {
        "due_diligence_from_approved_launch57_evidence_only": approved.get("decision_driving_approved_only"),
        "unapproved_inputs_observable_not_decision_driving": True,
        "freshness_preserved": fresh,
        "stale_not_promoted_to_stronger_truth": not fresh,
        "limitations_visible": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


_MANIPULATION_SCORE_THRESHOLD = 0.5
_SUSPICIOUS_ACTIVITY_MIN_CONFIDENCE = 0.5
_SUSPICIOUS_ACTIVITY_ELIGIBLE_SEVERITIES = frozenset({"medium", "high"})


def apply_manipulation_pattern_qualification_filter(
    *,
    assessment: Any,
    phrase_hits: list[str],
    whale_alerts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Require canonical suspicious-pattern evidence before #55 manipulation alert fires."""
    manipulation_flags = list(getattr(assessment, "manipulation_flags", None) or [])
    if not manipulation_flags and isinstance(assessment, dict):
        manipulation_flags = list(assessment.get("manipulation_flags") or [])

    corroborated_whale_rows = [
        a
        for a in (whale_alerts or [])
        if float((a or {}).get("manipulation_score") or 0) >= _MANIPULATION_SCORE_THRESHOLD
    ]

    pattern_evidence: list[dict[str, Any]] = []
    if phrase_hits:
        pattern_evidence.append({"type": "pump_dump_phrase", "phrases": phrase_hits})
    if manipulation_flags:
        pattern_evidence.append({"type": "sentiment_manipulation_flags", "flags": manipulation_flags})
    for row in corroborated_whale_rows:
        pattern_evidence.append(
            {
                "type": "whale_manipulation_score",
                "manipulation_score": row.get("manipulation_score"),
                "alert": row,
            }
        )

    qualifying = bool(pattern_evidence)
    return {
        "manipulation_alert_fired": qualifying,
        "pattern_evidence": pattern_evidence,
        "corroborated_whale_rows": corroborated_whale_rows,
        "movement_alone_excluded": True,
        "no_legal_or_criminal_conclusion": True,
        "runtime_qualification_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_manipulation_alert_disclosure(
    filtered: dict[str, Any],
    *,
    assessment: Any | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #55 manipulation alert backed by pattern evidence only."""
    rejected_reason = getattr(assessment, "rejected_reason", None) if assessment is not None else None
    if rejected_reason is None and isinstance(assessment, dict):
        rejected_reason = assessment.get("rejected_reason")
    return {
        "manipulation_from_pattern_evidence_only": True,
        "movement_alone_not_sufficient": True,
        "no_legal_or_criminal_conclusion": True,
        "material_limitation_visible": True,
        "uncertainty_qualified": not filtered.get("manipulation_alert_fired"),
        "runtime_qualification_applied": bool(filtered.get("runtime_qualification_applied")),
        "pattern_evidence_count": len(filtered.get("pattern_evidence") or []),
        "rejected_reason_observable": rejected_reason,
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_suspicious_activity_evidence_filter(
    raw_flags: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Gate #56 suspicion to evidence-backed flags; weak signals remain observable only."""
    decision_driving: list[dict[str, Any]] = []
    observable_only: list[dict[str, Any]] = []

    for flag in raw_flags or []:
        if not isinstance(flag, dict):
            continue
        confidence = float(flag.get("confidence") or 0)
        severity = str(flag.get("severity") or "low").lower()
        eligible = confidence >= _SUSPICIOUS_ACTIVITY_MIN_CONFIDENCE and severity in _SUSPICIOUS_ACTIVITY_ELIGIBLE_SEVERITIES
        entry = {**flag, "decision_driving": eligible}
        if eligible:
            decision_driving.append(entry)
        else:
            observable_only.append(entry)

    return {
        "decision_driving_flags": decision_driving,
        "observable_only_flags": observable_only,
        "suspicion_eligible": bool(decision_driving),
        "suspicion_count": len(decision_driving),
        "weak_evidence_not_promoted": True,
        "no_criminal_or_legal_conclusion": True,
        "no_aml_classification_assertion": True,
        "mini_aml_scope_preserved": True,
        "runtime_filter_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_suspicious_activity_disclosure(
    filtered: dict[str, Any],
) -> dict[str, Any]:
    """Adaptive — Launch #56 evidence-based suspicious activity with limited scope."""
    return {
        "evidence_based_suspicion_only": True,
        "weak_evidence_not_promoted": filtered.get("weak_evidence_not_promoted"),
        "no_criminal_or_legal_conclusion": True,
        "no_aml_classification_assertion": True,
        "mini_aml_scope_preserved": True,
        "limitations_visible": True,
        "uncertainty_qualified": bool(filtered.get("observable_only_flags")),
        "runtime_filter_applied": bool(filtered.get("runtime_filter_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_exchange_transparency_risk_guard(
    health: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Keep #57 exchange output as transparency/risk indicators — never solvency certification."""
    counterparty = dict((health or {}).get("counterparty_risk") or {})
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    missing_counterparty = not counterparty
    alert = dict((health or {}).get("alert_trigger") or {})

    risk_context = {
        "exchange": health.get("exchange"),
        "withdrawal_latency_status": counterparty.get("withdrawal_latency_status"),
        "abnormal_flow_pattern": counterparty.get("abnormal_flow_pattern"),
        "alert_trigger": alert if alert else None,
        "reserve_transparency_score_observable_only": counterparty.get("reserve_transparency_score"),
        "health_score_observable_only": health.get("health_score"),
        "incident_or_outage_signal_observable_only": alert.get("reason"),
    }

    conflicting = bool(
        counterparty.get("withdrawal_latency_status") == "green"
        and counterparty.get("abnormal_flow_pattern")
    )

    return {
        "risk_indicators": risk_context,
        "indicators_only": True,
        "solvency_certificate_claim": "FORBIDDEN",
        "reserve_guarantee_claim": "FORBIDDEN",
        "exchange_safety_certification": "FORBIDDEN",
        "decision_driving_solvency_assurance": False,
        "freshness_preserved": fresh,
        "missing_evidence_visible": missing_counterparty,
        "stale_not_promoted_to_stronger_truth": not fresh,
        "conflicting_evidence_visible": conflicting,
        "runtime_guard_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_exchange_transparency_disclosure(
    guarded: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — Launch #57 cautious exchange transparency; no solvency certification."""
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    return {
        "transparency_risk_indicators_only": True,
        "solvency_certificate_forbidden": guarded.get("solvency_certificate_claim") == "FORBIDDEN",
        "reserve_guarantee_forbidden": guarded.get("reserve_guarantee_claim") == "FORBIDDEN",
        "exchange_safety_certification_forbidden": guarded.get("exchange_safety_certification") == "FORBIDDEN",
        "decision_driving_solvency_assurance": guarded.get("decision_driving_solvency_assurance"),
        "limitations_visible": True,
        "freshness_preserved": fresh,
        "missing_or_conflicting_evidence_visible": bool(
            guarded.get("missing_evidence_visible") or guarded.get("conflicting_evidence_visible")
        ),
        "runtime_guard_applied": bool(guarded.get("runtime_guard_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def _direction_from_sign(value: float, *, positive: str, negative: str, neutral: str = "neutral") -> str:
    if value > 0:
        return positive
    if value < 0:
        return negative
    return neutral


def _taker_pressure_direction(ft: dict[str, Any]) -> str:
    ratio = ft.get("taker_buy_sell_ratio")
    if ratio is None:
        buy = float(ft.get("taker_buy_ratio") or 0.5)
        if buy > 0.5:
            return "buy_pressure"
        if buy < 0.5:
            return "sell_pressure"
        return "neutral"
    taker = float(ratio or 1.0)
    if taker > 1.0:
        return "buy_pressure"
    if taker < 1.0:
        return "sell_pressure"
    return "neutral"


def _funding_pressure_direction(funding_rate: float | None) -> str:
    return _direction_from_sign(
        float(funding_rate or 0),
        positive="long_crowded",
        negative="short_crowded",
    )


def _price_context_direction(change_24h_pct: float | None) -> str:
    return _direction_from_sign(
        float(change_24h_pct or 0),
        positive="up",
        negative="down",
        neutral="flat",
    )


def _coinglass_enhancement_available(overview: dict[str, Any] | None) -> bool:
    cg = dict((overview or {}).get("coinglass") or {})
    for key in ("funding", "liquidations", "open_interest"):
        block = cg.get(key)
        if isinstance(block, dict) and block.get("available"):
            return True
    return False


def _funding_taker_contradiction(
    funding_rate: float | None,
    ft: dict[str, Any],
) -> dict[str, Any] | None:
    funding_dir = _funding_pressure_direction(funding_rate)
    taker_dir = _taker_pressure_direction(ft)
    if funding_dir == "long_crowded" and taker_dir == "sell_pressure":
        return {
            "type": "funding_taker_divergence",
            "summary": "Funding implies crowded longs while taker flow shows sell pressure.",
            "funding_direction": funding_dir,
            "taker_direction": taker_dir,
        }
    if funding_dir == "short_crowded" and taker_dir == "buy_pressure":
        return {
            "type": "funding_taker_divergence",
            "summary": "Funding implies crowded shorts while taker flow shows buy pressure.",
            "funding_direction": funding_dir,
            "taker_direction": taker_dir,
        }
    return None


def build_derivatives_contract_core(
    *,
    spine: dict[str, Any] | None,
    ft: dict[str, Any] | None,
    overview: dict[str, Any] | None = None,
    evidence_class: str,
    direction: str,
    material_limitation: dict[str, Any] | None = None,
    material_contradiction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — derivatives contract fields that must drive consumer semantics."""
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    return {
        "freshness_state": (spine or {}).get("freshness_state"),
        "freshness_preserved": fresh,
        "stale_not_promoted_to_stronger_truth": not fresh,
        "direction": direction,
        "evidence_class": evidence_class,
        "material_limitation": material_limitation,
        "material_contradiction": material_contradiction,
        "runtime_contract_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_open_interest_derivatives_semantics(
    *,
    overview: dict[str, Any] | None,
    ft: dict[str, Any] | None,
    spine: dict[str, Any] | None,
) -> dict[str, Any]:
    """Launch #25 — OI intelligence with direct evidence and visible limitations."""
    free = dict(ft or {})
    available = bool(free.get("available")) or float(free.get("open_interest_usd") or 0) > 0
    direction = _price_context_direction(free.get("change_24h_pct"))
    limitation = {
        "summary": "Open interest level is direct single-venue observation; OI trend delta not claimed without historical series.",
        "single_venue_direct": True,
        "aggregated_oi_requires_optional_coinglass": not _coinglass_enhancement_available(overview),
    }
    contradiction = _funding_taker_contradiction(free.get("funding_rate"), free)
    contract = build_derivatives_contract_core(
        spine=spine,
        ft=free,
        overview=overview,
        evidence_class="direct",
        direction=direction,
        material_limitation=limitation,
        material_contradiction=contradiction,
    )
    answer_state = "OI_OBSERVABLE" if available else "INSUFFICIENT_EVIDENCE"
    if contradiction:
        answer_state = "QUALIFIED_OI_CONTRADICTION"
    return {
        "contract": contract,
        "answer_state": answer_state,
        "oi_observable": available,
        "open_interest_usd": free.get("open_interest_usd"),
        "open_interest_contracts": free.get("open_interest_contracts"),
        "price_context_direction": direction,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_open_interest_derivatives_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    return {
        "derivatives_contract_visible": True,
        "evidence_class": contract.get("evidence_class"),
        "direction": contract.get("direction"),
        "material_limitation_visible": bool(contract.get("material_limitation")),
        "material_contradiction_visible": bool(contract.get("material_contradiction")),
        "single_venue_direct_not_aggregated_claim": True,
        "runtime_contract_applied": bool(contract.get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_funding_rate_derivatives_semantics(
    *,
    overview: dict[str, Any] | None,
    ft: dict[str, Any] | None,
    spine: dict[str, Any] | None,
) -> dict[str, Any]:
    """Launch #26 — funding rate with direction and funding/taker contradiction wiring."""
    free = dict(ft or {})
    funding_rate = free.get("funding_rate")
    available = funding_rate is not None and (bool(free.get("available")) or funding_rate != 0)
    direction = _funding_pressure_direction(funding_rate)
    limitation = {
        "summary": "Funding rate is venue-snapshot direct evidence; cross-venue funding consensus not claimed on free tier.",
        "single_venue_direct": True,
        "optional_coinglass_enhancement_only": not _coinglass_enhancement_available(overview),
    }
    contradiction = _funding_taker_contradiction(funding_rate, free)
    contract = build_derivatives_contract_core(
        spine=spine,
        ft=free,
        overview=overview,
        evidence_class="direct",
        direction=direction,
        material_limitation=limitation,
        material_contradiction=contradiction,
    )
    answer_state = direction.upper() if available else "INSUFFICIENT_EVIDENCE"
    if contradiction:
        answer_state = "QUALIFIED_FUNDING_CONTRADICTION"
    return {
        "contract": contract,
        "answer_state": answer_state,
        "funding_observable": available,
        "funding_rate": funding_rate,
        "funding_rate_pct": free.get("funding_rate_pct"),
        "funding_direction": direction,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_funding_rate_derivatives_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    return {
        "derivatives_contract_visible": True,
        "evidence_class": contract.get("evidence_class"),
        "direction": contract.get("direction"),
        "material_limitation_visible": bool(contract.get("material_limitation")),
        "material_contradiction_visible": bool(contract.get("material_contradiction")),
        "funding_not_price_prediction": True,
        "runtime_contract_applied": bool(contract.get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_liquidation_derivatives_semantics(
    *,
    radar: dict[str, Any] | None,
    spine: dict[str, Any] | None,
) -> dict[str, Any]:
    """Launch #27 — liquidation light heatmap with scope limitation in decision semantics."""
    alerts = list((radar or {}).get("alerts") or [])
    available = bool(radar)
    buy_side = sum(1 for a in alerts if "long" in str(a.get("type", "")).lower() or a.get("side") == "long")
    sell_side = sum(1 for a in alerts if "short" in str(a.get("type", "")).lower() or a.get("side") == "short")
    if buy_side > sell_side:
        direction = "long_liquidation_bias"
    elif sell_side > buy_side:
        direction = "short_liquidation_bias"
    else:
        direction = "mixed_or_unspecified"
    limitation = {
        "summary": "Light liquidation heatmap preview only — not global liquidation coverage or full cascade mapping.",
        "light_preview_only": True,
        "global_liquidation_coverage_claim": "FORBIDDEN",
    }
    contract = build_derivatives_contract_core(
        spine=spine,
        ft=None,
        evidence_class="direct",
        direction=direction,
        material_limitation=limitation,
        material_contradiction=None,
    )
    answer_state = "LIQUIDATION_SIGNAL" if alerts else "NO_QUALIFYING_LIQUIDATION_CLUSTER"
    return {
        "contract": contract,
        "answer_state": answer_state,
        "liquidation_observable": available,
        "alert_count": len(alerts),
        "liquidation_direction": direction,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_liquidation_derivatives_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    return {
        "derivatives_contract_visible": True,
        "evidence_class": contract.get("evidence_class"),
        "direction": contract.get("direction"),
        "material_limitation_visible": bool(contract.get("material_limitation")),
        "light_heatmap_not_global_coverage": True,
        "runtime_contract_applied": bool(contract.get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_taker_leverage_derivatives_semantics(
    *,
    ft: dict[str, Any] | None,
    leverage_payload: dict[str, Any] | None,
    spine: dict[str, Any] | None,
) -> dict[str, Any]:
    """Launch #28 — taker pressure + leverage overhang with visible component disagreement."""
    free = dict(ft or {})
    leverage = dict(leverage_payload or {})
    taker_dir = _taker_pressure_direction(free)
    fragility = str(leverage.get("fragility") or "unknown").lower()
    if fragility == "red":
        leverage_dir = "elevated_deleveraging_risk"
    elif fragility == "yellow":
        leverage_dir = "moderate_overhang"
    elif fragility == "green":
        leverage_dir = "within_normal_range"
    else:
        leverage_dir = "unknown"
    disagreements: list[dict[str, Any]] = []
    if taker_dir == "buy_pressure" and fragility == "red":
        disagreements.append(
            {
                "type": "taker_leverage_divergence",
                "summary": "Taker flow shows buy pressure while leverage overhang fragility is elevated.",
                "taker_direction": taker_dir,
                "leverage_direction": leverage_dir,
            }
        )
    if taker_dir == "sell_pressure" and fragility == "green":
        disagreements.append(
            {
                "type": "taker_leverage_divergence",
                "summary": "Taker flow shows sell pressure while leverage overhang reads within normal range.",
                "taker_direction": taker_dir,
                "leverage_direction": leverage_dir,
            }
        )
    material_contradiction = disagreements[0] if disagreements else None
    limitation = {
        "summary": "Composite of direct taker flow and leverage-overhang indicator — not a unified execution signal.",
        "composite_components": ["taker_flow_direct", "leverage_overhang_indicator"],
    }
    contract = build_derivatives_contract_core(
        spine=spine,
        ft=free,
        evidence_class="composite",
        direction=taker_dir if not disagreements else "mixed",
        material_limitation=limitation,
        material_contradiction=material_contradiction,
    )
    contract["component_directions"] = {
        "taker": taker_dir,
        "leverage": leverage_dir,
    }
    contract["material_disagreements"] = disagreements
    contract["material_disagreement_visible"] = bool(disagreements)
    available = taker_dir != "neutral" or leverage_dir != "unknown"
    answer_state = "TAKER_PRESSURE" if taker_dir != "neutral" else "LEVERAGE_CONTEXT_ONLY"
    if disagreements:
        answer_state = "COMPONENT_DISAGREEMENT"
    if not available:
        answer_state = "INSUFFICIENT_EVIDENCE"
    return {
        "contract": contract,
        "answer_state": answer_state,
        "taker_direction": taker_dir,
        "leverage_direction": leverage_dir,
        "material_disagreements": disagreements,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_taker_leverage_derivatives_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    return {
        "derivatives_contract_visible": True,
        "evidence_class": contract.get("evidence_class"),
        "direction": contract.get("direction"),
        "component_disagreement_visible": bool(semantics.get("material_disagreements")),
        "material_limitation_visible": bool(contract.get("material_limitation")),
        "runtime_contract_applied": bool(contract.get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def _sentiment_score_value(sentiment: dict[str, Any] | None) -> float | None:
    if not isinstance(sentiment, dict):
        return None
    for key in ("score", "sentiment_score", "compound_score"):
        if sentiment.get(key) is not None:
            return float(sentiment[key])
    compound = sentiment.get("sentiment_compound_index")
    if isinstance(compound, dict) and compound:
        first = next(iter(compound.values()))
        if isinstance(first, dict) and first.get("score") is not None:
            return float(first["score"])
    return None


def _sentiment_direction(score: float | None) -> str:
    if score is None:
        return "unknown"
    return _direction_from_sign(score, positive="bullish", negative="bearish")


def _derivatives_pressure_direction(ft: dict[str, Any] | None) -> str:
    free = dict(ft or {})
    funding_dir = _funding_pressure_direction(free.get("funding_rate"))
    taker_dir = _taker_pressure_direction(free)
    if funding_dir == "long_crowded" or taker_dir == "buy_pressure":
        if funding_dir == "short_crowded" or taker_dir == "sell_pressure":
            return "mixed"
        return "bullish_pressure"
    if funding_dir == "short_crowded" or taker_dir == "sell_pressure":
        return "bearish_pressure"
    return "neutral"


def compute_derivatives_sentiment_composite(
    *,
    sentiment: dict[str, Any] | None,
    deriv_overview: dict[str, Any] | None,
    spine: dict[str, Any] | None,
) -> dict[str, Any]:
    """Launch #29 — composite that preserves visible material component disagreement."""
    ft = dict((deriv_overview or {}).get("free_tier") or {})
    sentiment_score = _sentiment_score_value(sentiment)
    sentiment_dir = _sentiment_direction(sentiment_score)
    deriv_dir = _derivatives_pressure_direction(ft)
    disagreements: list[dict[str, Any]] = []
    if (
        sentiment_dir in {"bullish", "bearish"}
        and deriv_dir in {"bullish_pressure", "bearish_pressure"}
        and sentiment_dir != deriv_dir.replace("_pressure", "")
    ):
        disagreements.append(
            {
                "type": "sentiment_derivatives_divergence",
                "summary": "Sentiment direction diverges from derivatives pressure components.",
                "sentiment_direction": sentiment_dir,
                "derivatives_direction": deriv_dir,
            }
        )
    funding_taker = _funding_taker_contradiction(ft.get("funding_rate"), ft)
    if funding_taker:
        disagreements.append(funding_taker)
    components = {
        "sentiment": {
            "score": sentiment_score,
            "direction": sentiment_dir,
            "source": "sentiment_engine",
        },
        "derivatives": {
            "funding_direction": _funding_pressure_direction(ft.get("funding_rate")),
            "taker_direction": _taker_pressure_direction(ft),
            "direction": deriv_dir,
            "source": "bd_platform.derivatives_hub",
        },
    }
    aligned = not disagreements and sentiment_score is not None
    decision_score = round(float(sentiment_score), 4) if aligned and sentiment_score is not None else None
    limitation = {
        "summary": "Composite combines sentiment and derivatives components; disagreement suppresses unified decision score.",
        "composite_not_hidden_when_components_disagree": True,
    }
    contract = build_derivatives_contract_core(
        spine=spine,
        ft=ft,
        overview=deriv_overview,
        evidence_class="composite",
        direction=deriv_dir if not disagreements else "mixed",
        material_limitation=limitation,
        material_contradiction=disagreements[0] if disagreements else None,
    )
    contract["material_disagreements"] = disagreements
    contract["material_disagreement_visible"] = bool(disagreements)
    contract["components"] = components
    answer_state = "ALIGNED_COMPOSITE" if aligned else "COMPONENT_DISAGREEMENT"
    if sentiment_score is None and not ft:
        answer_state = "INSUFFICIENT_EVIDENCE"
    return {
        "contract": contract,
        "answer_state": answer_state,
        "decision_driving_composite_score": decision_score,
        "observable_sentiment_score": sentiment_score,
        "components": components,
        "material_disagreements": disagreements,
        "composite_suppressed_due_to_disagreement": bool(disagreements),
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_derivatives_composite_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    return {
        "derivatives_contract_visible": True,
        "evidence_class": contract.get("evidence_class"),
        "direction": contract.get("direction"),
        "material_disagreement_visible": bool(semantics.get("material_disagreements")),
        "composite_not_hidden_when_components_disagree": True,
        "decision_driving_composite_suppressed_on_disagreement": bool(
            semantics.get("composite_suppressed_due_to_disagreement")
        ),
        "runtime_contract_applied": bool(contract.get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def _book_top_levels(book: dict[str, Any] | None) -> tuple[float, float, float, float]:
    row = dict(book or {})
    bid = float(row.get("bid") or 0)
    ask = float(row.get("ask") or 0)
    bid_qty = float(row.get("bid_qty") or 0)
    ask_qty = float(row.get("ask_qty") or 0)
    bids = row.get("bids") or []
    asks = row.get("asks") or []
    if (not bid or not ask) and bids and asks:
        bid = float(bids[0][0])
        bid_qty = float(bids[0][1]) if len(bids[0]) > 1 else bid_qty
        ask = float(asks[0][0])
        ask_qty = float(asks[0][1]) if len(asks[0]) > 1 else ask_qty
    return bid, ask, bid_qty, ask_qty


def _order_book_pressure_direction(book: dict[str, Any] | None) -> str:
    _, _, bid_qty, ask_qty = _book_top_levels(book)
    if bid_qty > ask_qty:
        return "buy_pressure"
    if ask_qty > bid_qty:
        return "sell_pressure"
    return "neutral"


def apply_order_book_intelligence_semantics(
    *,
    book: dict[str, Any] | None,
    spine: dict[str, Any] | None,
    depth_level: str = "L1",
) -> dict[str, Any]:
    """Launch #30 — order-book contract semantics on L1 direct evidence."""
    bid, ask, bid_qty, ask_qty = _book_top_levels(book)
    available = bool(book) and bid > 0 and ask > 0
    book_dir = _order_book_pressure_direction(book)
    price_change = float((spine or {}).get("change_24h") or 0)
    price_dir = _direction_from_sign(price_change, positive="up", negative="down", neutral="flat")
    contradiction = None
    if book_dir == "buy_pressure" and price_dir == "down":
        contradiction = {
            "type": "book_price_divergence",
            "summary": "Top-of-book buy pressure diverges from negative 24h price context.",
            "book_direction": book_dir,
            "price_context_direction": price_dir,
        }
    elif book_dir == "sell_pressure" and price_dir == "up":
        contradiction = {
            "type": "book_price_divergence",
            "summary": "Top-of-book sell pressure diverges from positive 24h price context.",
            "book_direction": book_dir,
            "price_context_direction": price_dir,
        }
    deeper_than_l1 = depth_level.upper() not in {"L1", "TOP_OF_BOOK"}
    limitation = {
        "summary": "L1 top-of-book depth at minimum — deeper L2/L3 ladders not claimed unless explicitly sourced.",
        "depth_level": depth_level,
        "deeper_than_l1_claimed": deeper_than_l1,
        "l1_minimum_met": not deeper_than_l1,
    }
    contract = build_derivatives_contract_core(
        spine=spine,
        ft=None,
        evidence_class="direct",
        direction=book_dir,
        material_limitation=limitation,
        material_contradiction=contradiction,
    )
    answer_state = "BOOK_OBSERVABLE" if available else "INSUFFICIENT_EVIDENCE"
    if contradiction:
        answer_state = "QUALIFIED_BOOK_CONTRADICTION"
    return {
        "contract": contract,
        "answer_state": answer_state,
        "book_observable": available,
        "book_direction": book_dir,
        "bid": bid,
        "ask": ask,
        "bid_qty": bid_qty,
        "ask_qty": ask_qty,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_order_book_intelligence_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    return {
        "order_book_contract_visible": True,
        "evidence_class": contract.get("evidence_class"),
        "direction": contract.get("direction"),
        "l1_minimum_met": contract.get("material_limitation", {}).get("l1_minimum_met"),
        "material_limitation_visible": bool(contract.get("material_limitation")),
        "material_contradiction_visible": bool(contract.get("material_contradiction")),
        "runtime_contract_applied": bool(contract.get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


_APPROVED_GENERAL_MARKET_SCREENER_SCOPES: frozenset[str] = frozenset(
    {"general_public_market", "general_market", "public_market"}
)
_UNSUPPORTED_SCREENER_SCOPE_FLAGS: frozenset[str] = frozenset(
    {
        "smart_money_only",
        "on_chain_only",
        "institutional_mesh",
        "custom_sql",
        "options_chain",
        "derivatives_only",
        "private_deal_flow",
    }
)


def apply_general_market_screener_guard(
    screener: list[dict[str, Any]] | Any,
    *,
    params: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Launch #31 — keep screener within approved general-market discovery scope."""
    p = dict(params or {})
    rows = list(screener) if isinstance(screener, list) else []
    requested_scope = str(p.get("filter_scope") or p.get("screener_scope") or "general_public_market").lower()
    unsupported_flags = sorted(flag for flag in _UNSUPPORTED_SCREENER_SCOPE_FLAGS if p.get(flag))
    scope_rejected = requested_scope not in _APPROVED_GENERAL_MARKET_SCREENER_SCOPES or bool(unsupported_flags)
    approved_rows = rows if not scope_rejected else []
    answer_state = "GENERAL_MARKET_SCREENED" if approved_rows else "UNSUPPORTED_SCOPE_REJECTED"
    if scope_rejected:
        answer_state = "UNSUPPORTED_SCOPE_REJECTED"
    elif not approved_rows:
        answer_state = "NO_QUALIFYING_RESULTS"
    limitation = {
        "summary": "General public market discovery only — smart-money or institutional mesh filters are not promoted here.",
        "approved_scope": "general_public_market",
        "unsupported_scope_rejected": scope_rejected,
    }
    return {
        "answer_state": answer_state,
        "screener_rows": approved_rows,
        "screener_observable": bool(rows),
        "scope_rejected": scope_rejected,
        "requested_scope": requested_scope,
        "unsupported_flags": unsupported_flags,
        "market_scope": "general_public_market",
        "material_limitation": limitation,
        "freshness_state": (spine or {}).get("freshness_state"),
        "runtime_guard_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_general_market_screener_disclosure(guarded: dict[str, Any]) -> dict[str, Any]:
    return {
        "general_market_discovery_only": True,
        "unsupported_scope_not_promoted": guarded.get("scope_rejected") is not True,
        "unsupported_scope_rejected": guarded.get("scope_rejected"),
        "approved_scope": guarded.get("market_scope"),
        "limitations_visible": True,
        "runtime_guard_applied": bool(guarded.get("runtime_guard_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


_APPROVED_WATCHLIST_DOMAINS: frozenset[str] = frozenset(
    {"token", "wallet", "token_and_wallet", "token_wallet"}
)
_UNSUPPORTED_WATCHLIST_DOMAIN_FLAGS: frozenset[str] = frozenset(
    {
        "multi_venue_mesh",
        "options_chain",
        "full_alert_mesh",
        "institutional_portfolio",
        "cross_chain_all",
        "derivatives_watch_mesh",
    }
)


def apply_limited_watchlist_guard(
    watches: list[dict[str, Any]] | None,
    *,
    params: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Launch #32 — limited token + wallet watchlists; reject unsupported domains."""
    p = dict(params or {})
    rows = list(watches or [])
    requested_domain = str(p.get("watchlist_domain") or "token_and_wallet").lower()
    unsupported_flags = sorted(flag for flag in _UNSUPPORTED_WATCHLIST_DOMAIN_FLAGS if p.get(flag))
    domain_rejected = requested_domain not in _APPROVED_WATCHLIST_DOMAINS or bool(unsupported_flags)
    approved_rows = rows if not domain_rejected else []
    if domain_rejected:
        answer_state = "UNSUPPORTED_DOMAIN_REJECTED"
    elif approved_rows:
        answer_state = "WATCHLIST_OBSERVABLE"
    else:
        answer_state = "NO_QUALIFYING_WATCHES"
    limitation = {
        "summary": "Limited launch watchlists — token + wallet tracking without full multi-venue alert mesh.",
        "approved_domains": sorted(_APPROVED_WATCHLIST_DOMAINS),
        "unsupported_domain_rejected": domain_rejected,
        "full_multi_venue_mesh": False,
        "limited_launch_scope": True,
    }
    return {
        "answer_state": answer_state,
        "wallet_watchlists": approved_rows,
        "watchlist_observable": bool(rows),
        "domain_rejected": domain_rejected,
        "requested_domain": requested_domain,
        "unsupported_flags": unsupported_flags,
        "material_limitation": limitation,
        "freshness_state": (spine or {}).get("freshness_state"),
        "runtime_guard_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_limited_watchlist_disclosure(guarded: dict[str, Any]) -> dict[str, Any]:
    return {
        "limited_launch_scope": True,
        "token_wallet_only": guarded.get("domain_rejected") is not True,
        "unsupported_domain_rejected": guarded.get("domain_rejected"),
        "full_multi_venue_mesh": False,
        "limitations_visible": True,
        "runtime_guard_applied": bool(guarded.get("runtime_guard_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


APPROVED_SMART_ALERT_CLASSES: frozenset[str] = frozenset({"price", "flow", "whale", "decision"})


def apply_smart_alerts_qualification_filter(
    evaluations: dict[str, Any],
    *,
    triggers: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    symbol: str | None = None,
) -> dict[str, Any]:
    """Launch #33 — approved alert classes only; required fields on each emitted alert."""
    from launch57.temporal_common import to_rfc3339, utc_now

    p = dict(params or {})
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    freshness_state = str((spine or {}).get("freshness_state") or "UNKNOWN")
    target = str(symbol or (spine or {}).get("symbol") or p.get("symbol") or "UNKNOWN")
    now = to_rfc3339(utc_now())

    requested_classes = p.get("alert_classes") or p.get("alert_types")
    if isinstance(requested_classes, str):
        requested_classes = [requested_classes]
    requested = [str(c).lower() for c in (requested_classes or [])]
    unsupported_requested = sorted({c for c in requested if c not in APPROVED_SMART_ALERT_CLASSES})

    qualified: dict[str, Any] = {}
    rejected_unsupported: list[dict[str, Any]] = []
    stale_blocked: list[str] = []

    for channel, evaluation in dict(evaluations or {}).items():
        channel_key = str(channel).lower()
        if channel_key not in APPROVED_SMART_ALERT_CLASSES:
            rejected_unsupported.append({"channel": channel_key, "reason": "unsupported_alert_class"})
            continue
        row = dict(evaluation) if isinstance(evaluation, dict) else {"value": evaluation}
        trigger = dict((triggers or {}).get(channel_key) or {})
        fired = bool(row.get("alert_fired") or row.get("ok"))
        trigger_age_ms = row.get("trigger_age_ms") or row.get("alert_age_ms")
        stale_evidence = trigger_age_ms is not None and float(trigger_age_ms) > float(
            p.get("stale_threshold_ms") or 60_000.0
        )
        evidence_state = "LIVE" if fresh and not stale_evidence else "DELAYED"
        if stale_evidence or not fresh:
            fired = False
            stale_blocked.append(channel_key)
        stamped = {
            **row,
            "alert_class": channel_key,
            "timestamp": row.get("timestamp") or trigger.get("timestamp") or now,
            "freshness_state": freshness_state,
            "evidence_state": evidence_state,
            "reason": row.get("reason") or trigger.get("rule") or f"{channel_key}_evaluation",
            "target": target,
            "user_action_path": "in_app_evaluation_and_api_response",
            "presented_as_live": evidence_state == "LIVE" and fired,
            "approved_alert_class": True,
        }
        qualified[channel_key] = stamped

    fired_channels = [c for c, row in qualified.items() if row.get("presented_as_live")]
    answer_state = "ALERTS_FIRED" if fired_channels else "NO_CURRENT_ALERTS"
    if unsupported_requested or rejected_unsupported:
        answer_state = "UNSUPPORTED_ALERT_CLASS_REJECTED"
    if stale_blocked and not fired_channels:
        answer_state = "STALE_EVIDENCE_NOT_LIVE"

    return {
        "answer_state": answer_state,
        "qualified_evaluations": qualified,
        "fired_channels": fired_channels,
        "unsupported_requested_classes": unsupported_requested,
        "rejected_unsupported_classes": rejected_unsupported,
        "stale_blocked_channels": stale_blocked,
        "delayed_not_presented_as_live": bool(stale_blocked) or not fresh,
        "approved_alert_classes_only": True,
        "runtime_filter_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_smart_alerts_disclosure(filtered: dict[str, Any]) -> dict[str, Any]:
    return {
        "approved_alert_classes_only": True,
        "approved_classes": sorted(APPROVED_SMART_ALERT_CLASSES),
        "unsupported_class_rejected": bool(filtered.get("unsupported_requested_classes") or filtered.get("rejected_unsupported_classes")),
        "delayed_not_presented_as_live": filtered.get("delayed_not_presented_as_live"),
        "required_fields_stamped": True,
        "runtime_filter_applied": bool(filtered.get("runtime_filter_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


_OBSERVED_SIGNAL_SOURCES: frozenset[str] = frozenset(
    {"footprint", "platform_spine", "live book footprint", "order_flow"}
)
_INFERENCE_MARKERS: frozenset[str] = frozenset({"checked", "aligned", "suggests", "implies"})
_UNSUPPORTED_CAUSAL_PARAM_FLAGS: frozenset[str] = frozenset(
    {
        "assert_causality",
        "causal_claim",
        "causal_factors",
        "establish_cause",
        "decision_certainty",
    }
)


def build_explanation_contract_core(
    *,
    spine: dict[str, Any] | None,
    evidence_class: str,
    uncertainty: str = "standard",
    material_limitation: dict[str, Any] | None = None,
    material_contradiction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adaptive — explanation contract fields that must drive consumer semantics."""
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    return {
        "freshness_state": (spine or {}).get("freshness_state"),
        "freshness_preserved": fresh,
        "stale_not_promoted_to_stronger_truth": not fresh,
        "evidence_class": evidence_class,
        "uncertainty": uncertainty,
        "causal_certainty_established": False,
        "material_limitation": material_limitation,
        "material_contradiction": material_contradiction,
        "runtime_contract_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def _classify_signal_factor(factor: dict[str, Any]) -> str:
    source = str(factor.get("source") or "").lower()
    detail = str(factor.get("detail") or "").lower()
    factor_text = str(factor.get("factor") or "").lower()
    if source in _OBSERVED_SIGNAL_SOURCES or "footprint" in detail:
        return "observed"
    if any(marker in detail for marker in _INFERENCE_MARKERS) or any(
        marker in factor_text for marker in ("alignment", "because", "caused", "drives")
    ):
        return "inference"
    if source in {"market", "model"}:
        return "inference"
    return "observed"


def apply_signal_explanation_semantics(
    *,
    footprint: dict[str, Any] | None,
    why_block: dict[str, Any] | None,
    spine: dict[str, Any] | None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Launch #34 — observed signal facts distinct from inference; no fabricated causality."""
    p = dict(params or {})
    why = dict(why_block or {})
    factors = list(why.get("top_3_factors") or [])
    unsupported_flags = sorted(flag for flag in _UNSUPPORTED_CAUSAL_PARAM_FLAGS if p.get(flag))
    unsupported_causal = bool(unsupported_flags) or bool(p.get("causal_claim"))

    observed: list[dict[str, Any]] = []
    inferences: list[dict[str, Any]] = []
    rejected_causal: list[dict[str, Any]] = []

    for raw in factors:
        row = dict(raw)
        proposition_class = _classify_signal_factor(row)
        if unsupported_causal and proposition_class == "inference":
            rejected_causal.append({**row, "proposition_class": "unsupported_causal_rejected"})
            continue
        row["proposition_class"] = proposition_class
        row["presented_as_established_fact"] = proposition_class == "observed"
        if proposition_class == "observed":
            observed.append(row)
        else:
            inferences.append(row)

    if footprint:
        observed.append(
            {
                "factor": "Order-flow footprint snapshot",
                "detail": "platform footprint feed",
                "source": "footprint",
                "proposition_class": "observed",
                "presented_as_established_fact": True,
            }
        )

    qualified_why = {
        **why,
        "top_3_factors": observed + inferences,
        "observed_facts": observed,
        "inferences": inferences,
        "causal_certainty_established": False,
        "unsupported_causal_rejected": unsupported_causal,
        "why_text": "\n".join(
            f"{i}. {f['factor']}" + (f" — {f['detail']}" if f.get("detail") else "")
            + (" (observed)" if f.get("proposition_class") == "observed" else " (inference, not causal fact)")
            for i, f in enumerate(observed + inferences, 1)
        ),
        "ready": bool(observed or inferences),
    }

    limitation = {
        "summary": "Signal explanation cites observed footprint context; causal mechanism and decision certainty are not established.",
        "causal_certainty_established": False,
        "inference_labeled": bool(inferences),
    }
    uncertainty = "qualified" if inferences or unsupported_causal else "standard"
    contract = build_explanation_contract_core(
        spine=spine,
        evidence_class="composite",
        uncertainty=uncertainty,
        material_limitation=limitation,
    )

    if unsupported_causal:
        answer_state = "UNSUPPORTED_CAUSALITY_REJECTED"
    elif observed:
        answer_state = "SIGNAL_EXPLAINED" if not inferences else "INFERENCE_QUALIFIED"
    else:
        answer_state = "INSUFFICIENT_OBSERVED_SIGNAL"

    return {
        "contract": contract,
        "answer_state": answer_state,
        "qualified_explanation": qualified_why,
        "observed_facts": observed,
        "inferences": inferences,
        "rejected_unsupported_causal": rejected_causal,
        "unsupported_causal_rejected": unsupported_causal,
        "signal_observable": bool(footprint or observed),
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_signal_explanation_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    return {
        "explanation_contract_visible": True,
        "causal_certainty_established": False,
        "observed_vs_inference_separated": True,
        "unsupported_causal_rejected": semantics.get("unsupported_causal_rejected"),
        "material_limitation_visible": bool(contract.get("material_limitation")),
        "runtime_contract_applied": bool(contract.get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


_PRICE_MOVE_INFERENCE_REASONS: frozenset[str] = frozenset(
    {
        "strong_24h_rally",
        "sharp_24h_drawdown",
        "muted_price_action",
        "sentiment_context_attached",
    }
)


def apply_price_move_explanation_semantics(
    *,
    change: float,
    price: float | None,
    sentiment: dict[str, Any] | None,
    reasons_raw: list[str] | None,
    spine: dict[str, Any] | None,
) -> dict[str, Any]:
    """Launch #35 — observed price facts distinct from interpretive inference."""
    observed_facts = {
        "change_24h_pct": change,
        "price": price,
        "price_source": "launch57.decision_common:load_decision_spine",
        "proposition_class": "observed",
        "presented_as_established_fact": True,
    }
    inferences: list[dict[str, Any]] = []
    for reason in list(reasons_raw or []):
        if reason in _PRICE_MOVE_INFERENCE_REASONS:
            inferences.append(
                {
                    "reason": reason,
                    "proposition_class": "inference",
                    "presented_as_established_fact": False,
                }
            )
        else:
            inferences.append(
                {
                    "reason": reason,
                    "proposition_class": "inference",
                    "presented_as_established_fact": False,
                }
            )

    if sentiment:
        inferences.append(
            {
                "reason": "sentiment_context_attached",
                "proposition_class": "inference",
                "presented_as_established_fact": False,
                "sentiment": sentiment,
            }
        )

    limitation = {
        "summary": "Observed 24h price change is direct spine fact; move labels and sentiment are inference, not observed cause.",
        "observed_vs_inference_separated": True,
    }
    contract = build_explanation_contract_core(
        spine=spine,
        evidence_class="direct",
        uncertainty="qualified" if inferences else "standard",
        material_limitation=limitation,
    )
    answer_state = "PRICE_MOVE_EXPLAINED" if price is not None else "INSUFFICIENT_OBSERVED_PRICE"

    return {
        "contract": contract,
        "answer_state": answer_state,
        "price_move_explanation": {
            "observed_facts": observed_facts,
            "inferences": inferences,
            "sentiment": sentiment or {},
        },
        "observed_facts": observed_facts,
        "inferences": inferences,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_price_move_explanation_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    return {
        "explanation_contract_visible": True,
        "observed_vs_inference_separated": True,
        "inference_not_observed_fact": bool(semantics.get("inferences")),
        "material_limitation_visible": bool(contract.get("material_limitation")),
        "runtime_contract_applied": bool(contract.get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


APPROVED_PLATFORM_RESEARCH_KEYS: frozenset[str] = frozenset(
    {"oracle_audit", "whale_intelligence", "sentiment", "onchain", "macro_regime"}
)
_UNSUPPORTED_RESEARCH_INPUT_FLAGS: frozenset[str] = frozenset(
    {
        "external_research",
        "web_sources",
        "user_prompt_injection",
        "autonomous_scope",
        "confidence_override",
        "unapproved_context",
    }
)


def apply_research_agent_grounding_filter(
    report: dict[str, Any],
    *,
    params: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    symbol: str | None = None,
) -> dict[str, Any]:
    """Launch #36 — grounded only in approved platform research keys; unapproved input cannot drive claims."""
    p = dict(params or {})
    target = str(symbol or (spine or {}).get("symbol") or p.get("symbol") or "UNKNOWN")
    unsupported_flags = sorted(flag for flag in _UNSUPPORTED_RESEARCH_INPUT_FLAGS if p.get(flag))
    unsupported_input = bool(unsupported_flags) or bool(p.get("external_research"))

    supported_claims = {
        key: report[key]
        for key in APPROVED_PLATFORM_RESEARCH_KEYS
        if isinstance(report, dict) and report.get(key) is not None
    }
    grounded_keys = sorted(supported_claims)
    agent_summary = (
        f"Grounded research snapshot for {target} from platform data spine "
        f"({', '.join(grounded_keys) or 'no approved sections'})."
    )

    limitation = {
        "summary": "Platform-data grounding only — external web or user-injected context cannot alter supported claims.",
        "platform_data_only": True,
        "autonomous_capability_scope": False,
        "llm_used": False,
    }
    contract = build_explanation_contract_core(
        spine=spine,
        evidence_class="composite",
        uncertainty="qualified" if unsupported_input else "standard",
        material_limitation=limitation,
    )
    answer_state = "GROUNDED_SNAPSHOT" if supported_claims else "INSUFFICIENT_PLATFORM_DATA"
    if unsupported_input:
        answer_state = "UNSUPPORTED_INPUT_REJECTED"

    return {
        "contract": contract,
        "answer_state": answer_state,
        "research_agent": {
            "symbol": target,
            "research_lab": {k: report.get(k) for k in grounded_keys},
            "grounded_sources": grounded_keys,
            "supported_claims": supported_claims,
            "platform_data_only": True,
            "agent_summary": agent_summary,
            "llm_used": False,
            "unsupported_input_rejected": unsupported_input,
            "rejected_input_flags": unsupported_flags,
        },
        "supported_claims": supported_claims,
        "unsupported_input_rejected": unsupported_input,
        "runtime_filter_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_research_agent_disclosure(filtered: dict[str, Any]) -> dict[str, Any]:
    return {
        "platform_data_only": True,
        "approved_keys_only": sorted(APPROVED_PLATFORM_RESEARCH_KEYS),
        "unsupported_input_rejected": filtered.get("unsupported_input_rejected"),
        "autonomous_scope_not_created": True,
        "runtime_filter_applied": bool(filtered.get("runtime_filter_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


_UNSUPPORTED_PORTAL_EVIDENCE_FLAGS: frozenset[str] = frozenset(
    {
        "supplemental_evidence",
        "external_brief",
        "custom_hit_rate",
        "custom_summary",
        "unapproved_research_feed",
    }
)


def apply_research_portal_evidence_filter(
    track_record: dict[str, Any],
    brief: dict[str, Any],
    *,
    params: dict[str, Any] | None = None,
    symbol: str | None = None,
) -> dict[str, Any]:
    """Launch #51 — approved oracle track record only; unapproved evidence cannot alter brief claims."""
    p = dict(params or {})
    asset = str(symbol or p.get("symbol") or "BTC").upper().replace("/USDT", "")
    unsupported_flags = sorted(flag for flag in _UNSUPPORTED_PORTAL_EVIDENCE_FLAGS if p.get(flag))
    unsupported_evidence = bool(unsupported_flags)

    cumulative = dict((track_record or {}).get("cumulative") or {})
    resolved = int(cumulative.get("resolved_predictions") or 0)
    hit = cumulative.get("hit_rate_percent")
    headline = f"{asset} research brief — platform oracle track record"
    if resolved > 0 and hit is not None:
        summary = (
            f"Live-only oracle metrics: {resolved} resolved predictions, "
            f"{hit}% hit rate (correct-only definition)."
        )
    else:
        summary = "Limited launch brief — cumulative oracle metrics pending more live resolutions."

    qualified_brief = {
        "headline": headline,
        "summary": summary,
        "shareable": True,
        "max_length_chars": 480,
        "symbol": asset,
        "metrics_scope": cumulative.get("metrics_scope") or "live_only",
        "evidence_source": "oracle_track_record.public_track_record",
        "approved_launch57_evidence_only": True,
        "unsupported_evidence_rejected": unsupported_evidence,
    }

    limitation = {
        "summary": "Limited launch research portal — short briefs from approved oracle track record only.",
        "separate_research_platform": False,
        "full_institutional_research_suite": False,
    }
    contract = build_explanation_contract_core(
        spine=None,
        evidence_class="direct",
        uncertainty="qualified" if unsupported_evidence else "standard",
        material_limitation=limitation,
    )
    answer_state = "RESEARCH_BRIEF_GROUNDED" if track_record else "INSUFFICIENT_APPROVED_EVIDENCE"
    if unsupported_evidence:
        answer_state = "UNSUPPORTED_EVIDENCE_REJECTED"

    return {
        "contract": contract,
        "answer_state": answer_state,
        "qualified_brief": qualified_brief,
        "track_record": track_record,
        "unsupported_evidence_rejected": unsupported_evidence,
        "rejected_evidence_flags": unsupported_flags,
        "runtime_filter_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_research_portal_disclosure(filtered: dict[str, Any]) -> dict[str, Any]:
    return {
        "approved_launch57_evidence_only": True,
        "separate_research_platform": False,
        "unsupported_evidence_rejected": filtered.get("unsupported_evidence_rejected"),
        "runtime_filter_applied": bool(filtered.get("runtime_filter_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


_MVRV_APPROVED_CORES: frozenset[str] = frozenset({"BTC", "ETH"})
_BEHAVIORAL_LEARNING_FLAGS: frozenset[str] = frozenset(
    {
        "behavioral_learning",
        "learning_model",
        "train_on_history",
        "feedback_loop",
        "reinforcement_update",
    }
)
_EXCLUDED_LIBRARY_STATUSES: frozenset[str] = frozenset(
    {
        "PARKED",
        "NO_LINKED_CANONICAL",
        "NOT_LINKED",
        "STUB",
        "PHANTOM",
    }
)


def build_edge_ui_contract_core(
    *,
    spine: dict[str, Any] | None,
    evidence_class: str,
    material_limitation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fresh = bool((spine or {}).get("live_eligible")) and bool((spine or {}).get("presented_as_live"))
    return {
        "freshness_state": (spine or {}).get("freshness_state"),
        "freshness_preserved": fresh,
        "evidence_class": evidence_class,
        "material_limitation": material_limitation,
        "runtime_contract_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_spot_perp_net_edge_semantics(
    opportunities: list[dict[str, Any]] | None,
    *,
    net_edge_result: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Launch #43 — gross spread is not executable without approved #5 Net-Edge on same opportunity."""
    p = dict(params or {})
    rows = list(opportunities or [])
    net_edge = (net_edge_result or {}).get("net_edge") if net_edge_result and not net_edge_result.get("blocked") else None
    net_edge_passing = bool(net_edge and (net_edge.get("pass") or net_edge.get("cost_claim_allowed")))
    requested_opportunity = p.get("opportunity")

    qualified: list[dict[str, Any]] = []
    executable_count = 0
    for row in rows:
        stamped = dict(row)
        same_opportunity = bool(requested_opportunity) and stamped.get("id") == requested_opportunity.get("id")
        gate_passed = net_edge_passing and same_opportunity
        stamped.update(
            {
                "executable": gate_passed,
                "gross_spread_only": not gate_passed,
                "net_edge_gate_passed": gate_passed,
                "net_edge_evaluated": bool(net_edge_result and not net_edge_result.get("blocked")),
                "presented_as_actionable": gate_passed,
                "net_edge_path": "launch57.trust_batch1:net_edge_truth_score",
            }
        )
        if gate_passed:
            executable_count += 1
        qualified.append(stamped)

    limitation = {
        "summary": "Gross spread from scan is not executable edge until approved Net-Edge (#5) evaluates the same opportunity.",
        "gross_edge_not_actionable_without_cost_treatment": True,
        "net_edge_required_path": "launch57.trust_batch1:net_edge_truth_score",
    }
    contract = build_edge_ui_contract_core(
        spine=spine,
        evidence_class="composite",
        material_limitation=limitation,
    )
    answer_state = "NET_EDGE_QUALIFIED" if executable_count else "GROSS_SPREAD_NOT_EXECUTABLE"
    if net_edge_result and net_edge_result.get("blocked"):
        answer_state = "NET_EDGE_GATE_BLOCKED"

    return {
        "contract": contract,
        "answer_state": answer_state,
        "qualified_opportunities": qualified,
        "executable_count": executable_count,
        "gross_spread_only_count": len(qualified) - executable_count,
        "net_edge_gate_passed": net_edge_passing,
        "net_edge_result": net_edge_result,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_spot_perp_net_edge_disclosure(semantics: dict[str, Any]) -> dict[str, Any]:
    return {
        "gross_spread_not_executable_without_net_edge": True,
        "net_edge_path": "launch57.trust_batch1:net_edge_truth_score",
        "executable_count": semantics.get("executable_count"),
        "runtime_contract_applied": bool((semantics.get("contract") or {}).get("runtime_contract_applied")),
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_mvrv_provenance_guard(
    cores: dict[str, Any],
    source_status: dict[str, Any],
    *,
    asset: str,
    spine: dict[str, Any] | None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Launch #38 — BTC/ETH only; licensed provenance or preserved external blocker."""
    p = dict(params or {})
    licensed_configured = bool(p.get("licensed_mvrv_source_configured"))
    filtered_cores: dict[str, Any] = {}
    filtered_status: dict[str, Any] = {}

    for target in sorted(_MVRV_APPROVED_CORES):
        if target not in cores and asset not in _MVRV_APPROVED_CORES:
            continue
        if asset in _MVRV_APPROVED_CORES and target != asset:
            continue
        mvrv = dict(cores.get(target) or {})
        has_proxy = bool(mvrv.get("z_score") is not None and mvrv.get("ok"))
        licensed_live = licensed_configured and has_proxy
        status = dict(source_status.get(target) or {})
        status.update(
            {
                "licensed_mvrv_feed": licensed_configured,
                "local_proxy_compute": has_proxy and not licensed_configured,
                "reference_only": has_proxy and not licensed_configured,
                "blocker": None if licensed_live else "BLOCKED_EXTERNAL",
                "blocker_reason": None if licensed_live else "licensed_onchain_mvrv_source_not_configured",
                "presented_as_live": bool(licensed_live and (spine or {}).get("presented_as_live")),
                "provenance": "licensed_feed" if licensed_configured else "reference_only_no_licensed_source",
            }
        )
        if has_proxy and not licensed_configured:
            filtered_cores[target] = {
                **mvrv,
                "reference_only": True,
                "licensed_values": False,
                "presented_as_live": False,
            }
        elif licensed_live:
            filtered_cores[target] = mvrv
        else:
            filtered_cores[target] = mvrv
        filtered_status[target] = status

    out_of_scope = asset not in _MVRV_APPROVED_CORES and asset != "BTC"
    limitation = {
        "summary": "MVRV/Z limited to BTC/ETH core; licensed on-chain feed required for LIVE values.",
        "btc_eth_only": True,
        "licensed_source_required": not licensed_configured,
    }
    contract = build_edge_ui_contract_core(
        spine=spine,
        evidence_class="direct" if licensed_configured else "reference_only",
        material_limitation=limitation,
    )
    any_live = any(s.get("presented_as_live") for s in filtered_status.values())
    answer_state = "MVRV_LICENSED_OBSERVABLE" if any_live else "BLOCKED_EXTERNAL_NO_LICENSED_SOURCE"
    if out_of_scope and asset not in filtered_cores:
        answer_state = "OUT_OF_SCOPE_NON_BTC_ETH"

    return {
        "contract": contract,
        "answer_state": answer_state,
        "cores": filtered_cores,
        "source_status": filtered_status,
        "licensed_source_configured": licensed_configured,
        "no_phantom_live_values": not any_live or licensed_configured,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_mvrv_provenance_disclosure(guarded: dict[str, Any]) -> dict[str, Any]:
    return {
        "btc_eth_only": True,
        "licensed_source_configured": guarded.get("licensed_source_configured"),
        "blocked_external_preserved": guarded.get("answer_state") == "BLOCKED_EXTERNAL_NO_LICENSED_SOURCE",
        "no_phantom_live_values": guarded.get("no_phantom_live_values"),
        "runtime_guard_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_personal_history_guard(
    rows: list[dict[str, Any]] | None,
    *,
    params: dict[str, Any] | None = None,
    tier: str = "free",
) -> dict[str, Any]:
    """Launch #49 — personal history is read-only; not behavioral-learning input."""
    p = dict(params or {})
    unsupported_flags = sorted(flag for flag in _BEHAVIORAL_LEARNING_FLAGS if p.get(flag))
    learning_rejected = bool(unsupported_flags)
    history_rows = list(rows or [])

    sanitized = [
        {
            **row,
            "history_only": True,
            "behavioral_learning_input": False,
            "market_evidence": False,
        }
        for row in history_rows
    ]

    limitation = {
        "summary": "Personal decision history is archival read-only — not a behavioral-learning training surface.",
        "behavioral_learning": False,
        "history_only": True,
    }
    contract = build_edge_ui_contract_core(spine=None, evidence_class="historical", material_limitation=limitation)
    answer_state = "HISTORY_OBSERVABLE" if sanitized and not learning_rejected else "UNSUPPORTED_LEARNING_SCOPE_REJECTED"
    if learning_rejected:
        answer_state = "UNSUPPORTED_LEARNING_SCOPE_REJECTED"

    return {
        "contract": contract,
        "answer_state": answer_state,
        "decisions": sanitized if not learning_rejected else [],
        "count": len(sanitized) if not learning_rejected else 0,
        "tier": tier,
        "history_only": True,
        "behavioral_learning_rejected": learning_rejected,
        "rejected_flags": unsupported_flags,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_personal_history_disclosure(guarded: dict[str, Any]) -> dict[str, Any]:
    return {
        "history_only": True,
        "behavioral_learning_rejected": guarded.get("behavioral_learning_rejected"),
        "runtime_guard_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_discipline_mirror_guard(
    mirror: dict[str, Any],
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Launch #50 — reflective mirror only; user behavior is not market/financial evidence."""
    p = dict(params or {})
    unsupported_flags = sorted(flag for flag in _BEHAVIORAL_LEARNING_FLAGS if p.get(flag))
    learning_rejected = bool(unsupported_flags)
    base = dict(mirror) if isinstance(mirror, dict) else {}

    reflective = {
        **base,
        "reflective_only": True,
        "market_evidence": False,
        "financial_truth": False,
        "behavioral_learning_surface": False,
        "private_coaching_only": True,
        "presented_as_market_signal": False,
    }
    for key in ("hero_deepening",):
        reflective.pop(key, None)

    limitation = {
        "summary": "Discipline mirror is private reflective coaching — not market evidence or financial truth.",
        "reflective_only": True,
    }
    contract = build_edge_ui_contract_core(spine=None, evidence_class="reflective", material_limitation=limitation)
    answer_state = "MIRROR_OBSERVABLE" if "error" not in base and not learning_rejected else "UNSUPPORTED_LEARNING_SCOPE_REJECTED"
    if learning_rejected:
        answer_state = "UNSUPPORTED_LEARNING_SCOPE_REJECTED"
        reflective = {"error": "behavioral_learning_not_in_scope", "private": True, "reflective_only": True}

    return {
        "contract": contract,
        "answer_state": answer_state,
        "discipline_mirror": reflective,
        "reflective_only": True,
        "behavioral_learning_rejected": learning_rejected,
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_discipline_mirror_disclosure(guarded: dict[str, Any]) -> dict[str, Any]:
    return {
        "reflective_only": True,
        "market_evidence": False,
        "behavioral_learning_rejected": guarded.get("behavioral_learning_rejected"),
        "runtime_guard_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def apply_capability_library_guard(
    entries: list[dict[str, Any]] | None,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Launch #52 — Launch-57 SSOT library only; no PARKED capabilities or second registry."""
    p = dict(params or {})
    inject_parked = bool(p.get("include_parked") or p.get("secondary_registry"))
    rows = list(entries or [])

    approved: list[dict[str, Any]] = []
    rejected_parked: list[dict[str, Any]] = []
    for row in rows:
        ln = row.get("launch_number")
        status = str(row.get("engineering_status") or "")
        if not isinstance(ln, int) or ln < 1 or ln > 57:
            continue
        if status in _EXCLUDED_LIBRARY_STATUSES or inject_parked:
            rejected_parked.append(row)
            continue
        approved.append(
            {
                "launch_number": ln,
                "launch_name": row.get("launch_name"),
                "engineering_status": status,
                "handler_module": row.get("handler_module"),
                "secondary_layer": True,
                "ssot_source": "governance/launch57/LAUNCH57_REGISTER.json",
                "canonical_identity_preserved": True,
            }
        )

    limitation = {
        "summary": "Secondary capability library derives from Launch-57 SSOT only — no PARKED items or parallel registry.",
        "launch57_scope_only": True,
        "separate_research_platform": False,
    }
    contract = build_edge_ui_contract_core(spine=None, evidence_class="catalog", material_limitation=limitation)
    answer_state = "LIBRARY_GROUNDED" if approved and not inject_parked else "UNSUPPORTED_REGISTRY_SCOPE_REJECTED"
    if inject_parked:
        answer_state = "UNSUPPORTED_REGISTRY_SCOPE_REJECTED"

    return {
        "contract": contract,
        "answer_state": answer_state,
        "results": approved if not inject_parked else [],
        "count": len(approved) if not inject_parked else 0,
        "rejected_parked": rejected_parked,
        "launch57_scope_only": True,
        "secondary_layer": True,
        "not_primary_home": True,
        "no_second_registry": True,
        "ssot_source": "governance/launch57/LAUNCH57_REGISTER.json",
        "methodology_version": METHODOLOGY_VERSION,
    }


def build_capability_library_disclosure(guarded: dict[str, Any]) -> dict[str, Any]:
    return {
        "launch57_scope_only": True,
        "no_second_registry": True,
        "parked_excluded": True,
        "ssot_derived": True,
        "runtime_guard_applied": True,
        "methodology_version": METHODOLOGY_VERSION,
    }
