"""Decision Truth product experience projection (P5).

Canonical flow: Governed Decision Truth → Product Projection → User Explanation.
No UI-side recomputation or parallel decision logic.
"""

from __future__ import annotations

from typing import Any

from decision_truth.product.calm_default import build_calm_default
from decision_truth.product.command_view import build_command_view
from decision_truth.product.daily_brief import build_daily_evidence_autopsy
from decision_truth.product.delivery import resolve_user_local_delivery
from decision_truth.product.evidence_trail import build_full_evidence_trail
from decision_truth.product.grounding import validate_material_claims
from decision_truth.product.no_decision import build_no_decision_surface
from decision_truth.product.reject_proof import build_reject_bad_opportunity_proof
from decision_truth.product.rejection_engine import build_rejection_engine, record_govern_rejection
from decision_truth.product.six_heroes import build_six_heroes
from decision_truth.product.smart_money import build_smart_money_context
from decision_truth.product.thirty_second import build_thirty_second_truth
from decision_truth.product.why_not import build_why_not_engine
from decision_truth.product.causality import sanitize_causal_language


def project_decision_product(
    payload: dict[str, Any],
    *,
    lang: str = "en",
    user_timezone: str | None = None,
    delivery_preferences: dict[str, Any] | None = None,
    command_view_enabled: bool = False,
) -> dict[str, Any]:
    """Attach canonical product experience surfaces to a governed payload."""
    out = dict(payload)
    dt = dict(out.get("decision_truth") or {})
    contract = dict(dt.get("contract") or {})
    state = str(out.get("decision_truth_state") or contract.get("decision_state") or "UNAVAILABLE")

    record_govern_rejection(out)

    why_not_engine = build_why_not_engine(out)
    dt["why_not"] = why_not_engine
    rejection_engine = build_rejection_engine(out)
    six_heroes = build_six_heroes(out)
    smart_money = build_smart_money_context(out)
    daily_brief = build_daily_evidence_autopsy(out, lang=lang)
    evidence_trail = build_full_evidence_trail(out)
    thirty_second = build_thirty_second_truth(out, six_heroes=six_heroes)
    no_decision = build_no_decision_surface(out, why_not_engine=why_not_engine)
    reject_proof = build_reject_bad_opportunity_proof(out)
    calm = build_calm_default(command_view_enabled=command_view_enabled)
    delivery = resolve_user_local_delivery(
        out,
        user_timezone=user_timezone,
        preferences=delivery_preferences,
    )
    command_view = build_command_view(out, enabled=command_view_enabled) if command_view_enabled else None

    material_claims = validate_material_claims(out)
    out = sanitize_causal_language(out)

    product = {
        "methodology_version": "dts-p5-product-experience-1.0",
        "rejection_engine": rejection_engine,
        "why_not_engine": why_not_engine,
        "six_heroes": six_heroes,
        "command_view": command_view,
        "smart_money_context": smart_money,
        "daily_evidence_autopsy": daily_brief,
        "material_claims": material_claims,
        "user_local_delivery": delivery,
        "reject_bad_opportunity": reject_proof,
        "no_decision": no_decision,
        "full_evidence_trail": evidence_trail,
        "thirty_second_truth": thirty_second,
        "calm_default": calm,
        "projection_source": "canonical_decision_truth",
        "no_parallel_logic": True,
    }
    dt["product_experience"] = product
    out["decision_truth"] = dt

    from data_governance.decision_surface import build_decision_surface

    out["todays_decision_surface"] = build_decision_surface(out, lang=lang)
    out["product_experience"] = product

    from decision_truth.cross_cutting import apply_cross_cutting_delivery

    out = apply_cross_cutting_delivery(out, lang=lang, user_timezone=user_timezone)
    return out


__all__ = ["project_decision_product"]
