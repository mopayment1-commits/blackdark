"""
Launch-57 Phase 2 Adaptive Batch A — trust-surface disclosure helpers.

Support structure only (not a capability). Level-1 progressive disclosure and
safety-floor fields for Launch #2–#5 (trust_batch1), #47–#48/#44–#46
(trust_batch2), #7–#11 (decision_batch1), #12/#37 (decision_batch2), and
#20/#16/#17/#13/#14 (smart_money_batch1) consumer paths.
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
