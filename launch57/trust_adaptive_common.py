"""
Launch-57 Phase 2 Adaptive Batch A — trust-surface disclosure helpers.

Support structure only (not a capability). Level-1 progressive disclosure and
safety-floor fields for Launch #2, #3, #4, #5 consumer paths in trust_batch1.
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
