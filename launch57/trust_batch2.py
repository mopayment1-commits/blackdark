"""
Launch-57 Phase 2 — Trust Batch 2 product surfaces.

Build order: #47 risk disclosure → #48 abstain/reject → #44 share card → #45 accuracy page → #46 guest trust
"""

from __future__ import annotations

from typing import Any

from launch57.evidence_class_common import assess_user_evidence_class, attach_evidence_class_metadata
from launch57.trust_adaptive_common import (
    attach_adaptive_disclosure,
    build_abstention_reject_disclosure,
    build_approved_public_trust_surfaces,
    build_level1_decision_disclosure,
    build_ledger_interpretation_context,
    build_material_risk_access,
    build_shareable_truth_context,
    validate_material_claims_from_payload,
)
from launch57.trust_batch1 import attach_trust_envelope

LAUNCH57_TRUST_BATCH2_ITEM_IDS: frozenset[int] = frozenset({47, 48, 44, 45, 46})
_B10_LAUNCH_ITEMS: frozenset[int] = frozenset({44, 45, 46})


def _finalize_trust_batch2_surface(
    body: dict[str, Any],
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    p = dict(params or {})
    wrapped = attach_trust_envelope(body)
    launch_id = int(body.get("launch_item_id") or 0)
    if launch_id not in _B10_LAUNCH_ITEMS:
        return wrapped
    from launch57.b10_shareable_public_bridge import finalize_b10_shareable_surface

    return finalize_b10_shareable_surface(
        wrapped,
        payload=p,
        display_timezone=p.get("display_timezone"),
    )


def _base_payload(params: dict[str, Any] | None, *, symbol: str) -> dict[str, Any]:
    p = dict(params or {})
    if p.get("governed_payload"):
        return dict(p["governed_payload"])
    return {
        "symbol": symbol,
        "decision_truth_state": p.get("decision_truth_state") or "UNAVAILABLE",
        "decision_action": p.get("decision_action") or "NO_DECISION",
        "decision_truth": p.get("decision_truth") or {},
        "net_edge_truth": p.get("net_edge_truth"),
    }


async def one_click_risk_disclosure(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #47 — one-click risk disclosure on every decision."""
    from decision_certificate import compliance_footer_block
    from decision_truth.product import project_decision_product
    from decision_truth.product.reject_proof import build_reject_bad_opportunity_proof

    payload = _base_payload(params, symbol=symbol)
    projected = project_decision_product(payload)
    reject_proof = build_reject_bad_opportunity_proof(payload)
    compliance = compliance_footer_block(
        surface="one_click_risk_disclosure",
        trust_basis="canonical_decision_record + public_accuracy_ledger",
    )
    product = projected.get("product_experience") or {}

    material_claims = product.get("material_claims") or validate_material_claims_from_payload(payload)
    material_risk = build_material_risk_access(material_claims, reject_proof=reject_proof)
    body = {
        "launch_item_id": 47,
        "surface": "one_click_risk_disclosure",
        "symbol": symbol,
        "success": True,
        "material_risk": material_risk,
        "risk_disclosure": {
            "compliance_footer": compliance,
            "reject_proof": reject_proof,
            "material_claims": material_claims,
            "material_risk": material_risk,
            "one_click": True,
            "derived_from": "canonical_govern_pipeline",
        },
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "one_click_risk_disclosure",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    wrapped = attach_trust_envelope(body)
    disclosure = build_level1_decision_disclosure(
        payload,
        launch_item_id=47,
        surface="one_click_risk_disclosure",
        answer_state=str(payload.get("decision_truth_state") or "RISK_DISCLOSED"),
        uncertainty="qualified",
    )
    return attach_adaptive_disclosure(
        wrapped,
        disclosure,
        extra={"material_risk": material_risk},
    )


async def abstain_reject_reasons_visible(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #48 — abstain/reject reasons visible (not hidden as errors)."""
    from decision_truth.product import project_decision_product
    from decision_truth.product.no_decision import build_no_decision_surface
    from decision_truth.product.rejection_engine import build_rejection_engine

    payload = _base_payload(params, symbol=symbol)
    projected = project_decision_product(payload)
    dp = projected.get("product_experience") or {}
    no_decision = dp.get("no_decision") or build_no_decision_surface(payload)
    rejection = dp.get("rejection_engine") or build_rejection_engine(payload)

    abstention_disclosure = build_abstention_reject_disclosure(
        payload,
        no_decision=no_decision,
        rejection=rejection,
    )
    body = {
        "launch_item_id": 48,
        "surface": "abstain_reject_reasons_visible",
        "symbol": symbol,
        "success": True,
        "no_decision": no_decision,
        "rejection_engine": rejection,
        "abstention_reject_disclosure": abstention_disclosure,
        "reasons_visible": True,
        "hidden_as_error": bool(no_decision.get("hidden_as_error")),
        "first_class_abstain": bool(no_decision.get("first_class_state")),
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "abstain_reject_reasons_visible",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    wrapped = attach_trust_envelope(body)
    disclosure = build_level1_decision_disclosure(
        payload,
        launch_item_id=48,
        surface="abstain_reject_reasons_visible",
        answer_state=str(no_decision.get("decision_action") or payload.get("decision_action") or "NO_DECISION"),
        uncertainty="insufficient_evidence",
    )
    return attach_adaptive_disclosure(
        wrapped,
        disclosure,
        extra={"abstention_reject_disclosure": abstention_disclosure},
    )


async def shareable_decision_card(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #44 — shareable decision/oracle card (OG metadata)."""
    from decision_certificate import build_decision_certificate
    from launch57.decision_timing_common import build_decision_timing_context

    p = dict(params or {})
    cert = build_decision_certificate(
        {
            "symbol": symbol,
            "tier": p.get("tier") or "free",
            "decision_action": p.get("decision_action") or "WAIT",
            "decision_sentence": p.get("decision_sentence") or f"{symbol} governed decision",
            "prediction_id": p.get("prediction_id"),
            "chain_hash": p.get("chain_hash"),
            "opportunity_score": p.get("opportunity_score"),
        }
    )
    evidence = assess_user_evidence_class(p, display_timezone=p.get("display_timezone"))
    timing = build_decision_timing_context(p, display_timezone=p.get("display_timezone"))
    timing_dict = timing.as_dict() if timing else {}
    material_claims = validate_material_claims_from_payload(p)
    shareable_truth = build_shareable_truth_context(
        p,
        evidence=evidence.to_payload(),
        material_claims=material_claims,
        timing=timing_dict,
    )
    og = {
        "title": f"BLACKDARK Decision · {symbol}",
        "description": cert.get("share_text") or cert.get("decision_sentence"),
        "image": f"/og/decision-card/{cert.get('certificate_hash', '')[:16]}.png",
        "url": cert.get("permalink"),
    }
    body = {
        "launch_item_id": 44,
        "surface": "shareable_decision_card",
        "symbol": symbol,
        "success": bool(cert.get("certificate_hash")),
        "certificate": cert,
        "share_urls": cert.get("share_urls"),
        "og_metadata": og,
        "shareable_truth_context": shareable_truth,
        "unsupported_live_claim_blocked": shareable_truth["unsupported_live_claim_blocked"],
        "alias_of": "CAP-0641",
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "shareable_decision_card",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    body = attach_evidence_class_metadata(body, display_timezone=p.get("display_timezone"))
    finalized = _finalize_trust_batch2_surface(body, params=p)
    disclosure = build_level1_decision_disclosure(
        p,
        launch_item_id=44,
        surface="shareable_decision_card",
        answer_state=str(p.get("decision_action") or cert.get("decision_action") or "WAIT"),
        evidence_display=finalized.get("evidence_display"),
        decision_timing=timing_dict,
    )
    return attach_adaptive_disclosure(
        finalized,
        disclosure,
        extra={"shareable_truth_context": shareable_truth},
    )


async def shareable_accuracy_page(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #45 — shareable accuracy/outcome page (alias of CAP-0640 live ledger)."""
    from launch57.public_accuracy_common import enrich_public_track_record
    from oracle_track_record import public_track_record

    p = dict(params or {})
    zone = str(p.get("display_timezone") or "UTC")
    ledger = public_track_record()
    enriched = enrich_public_track_record(ledger, display_timezone=zone)
    cumulative = enriched.get("cumulative") or {}
    interpretation = build_ledger_interpretation_context(enriched)
    page = {
        "href": "/oracle-accuracy",
        "permalink": "https://blackdark.app/oracle-accuracy",
        "title": "Public Accuracy Ledger",
        "hit_rate_percent": cumulative.get("hit_rate_percent"),
        "resolved_predictions": cumulative.get("resolved_predictions"),
        "metrics_scope": cumulative.get("metrics_scope") or "live_only",
        "synthetic_excluded": True,
    }
    body = {
        "launch_item_id": 45,
        "surface": "shareable_accuracy_page",
        "symbol": symbol,
        "success": True,
        "accuracy_page": page,
        "ledger": enriched,
        "public_accuracy_ledger": enriched,
        "ledger_interpretation_context": interpretation,
        "alias_of": "CAP-0640",
        "live_only_primary": enriched.get("live_only_primary", True),
        "metrics_scope": enriched.get("metrics_scope") or "live_only",
        "synthetic_excluded_from_primary": bool(
            (enriched.get("synthetic_demo_data") or {}).get("excluded_from_primary_metrics", True)
        ),
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "shareable_accuracy_page",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    finalized = _finalize_trust_batch2_surface(body, params=p)
    disclosure = build_level1_decision_disclosure(
        p,
        launch_item_id=45,
        surface="shareable_accuracy_page",
        answer_state="LIVE_PRIMARY_LEDGER",
        evidence_display=finalized.get("evidence_display"),
    )
    return attach_adaptive_disclosure(
        finalized,
        disclosure,
        extra={"ledger_interpretation_context": interpretation},
    )


async def guest_trust_surface(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #46 — guest/anonymous trust surface."""
    from launch57.anonymous_visitor_common import (
        attach_anonymous_visitor_envelope,
        build_anonymous_route_inventory,
        build_public_intelligence_proof_index,
        reference_anonymous_visitor_governance,
        verify_private_by_default,
    )

    p = dict(params or {})
    status = reference_anonymous_visitor_governance()
    approved_surfaces = build_approved_public_trust_surfaces()
    private_default = verify_private_by_default()
    public_proofs = build_public_intelligence_proof_index()
    route_inventory = build_anonymous_route_inventory()
    body = {
        "launch_item_id": 46,
        "surface": "guest_trust_surface",
        "symbol": symbol,
        "success": True,
        "approved_public_trust_surfaces": approved_surfaces,
        "guest_trust": {
            "anonymous_state": status.get("anonymous_state"),
            "private_by_default": status.get("private_by_default"),
            "public_readiness": status.get("public_readiness"),
            "rate_limits": status.get("rate_limits"),
            "no_pii_leak": status.get("no_pii_leak"),
            "visitor_tier_gating": status.get("visitor_tier_gating"),
            "route_inventory": status.get("route_inventory"),
            "launch57_route_inventory": route_inventory,
            "public_intelligence_proofs": public_proofs,
            "private_by_default_guard": private_default,
            "approved_public_trust_surfaces": approved_surfaces,
            "not_duplicate_private_app": True,
            "secondary_public_layer": True,
        },
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "guest_trust_surface",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    finalized = _finalize_trust_batch2_surface(body, params=p)
    disclosure = build_level1_decision_disclosure(
        p,
        launch_item_id=46,
        surface="guest_trust_surface",
        answer_state="GUEST_TRUST",
        uncertainty="qualified",
    )
    from launch57.identity_auth_common import attach_identity_auth_envelope

    disclosed = attach_adaptive_disclosure(
        finalized,
        disclosure,
        extra={
            "approved_public_trust_surfaces": approved_surfaces,
            "public_intelligence_proofs": public_proofs,
        },
    )
    from launch57.billing_entitlement_common import attach_billing_entitlement_envelope

    disclosed = attach_identity_auth_envelope(
        disclosed,
        launch_item_id=46,
        surface_type="public",
        params=p,
    )
    from launch57.compounding_evidence_common import attach_compounding_evidence_envelope

    disclosed = attach_billing_entitlement_envelope(disclosed, launch_item_id=46, params=p)
    disclosed = attach_compounding_evidence_envelope(disclosed, launch_item_id=46)
    return attach_anonymous_visitor_envelope(disclosed, launch_item_id=46, params=p)


_DISPATCH_BY_LAUNCH_ITEM: dict[int, str] = {
    47: "one_click_risk_disclosure",
    48: "abstain_reject_reasons_visible",
    44: "shareable_decision_card",
    45: "shareable_accuracy_page",
    46: "guest_trust_surface",
}


async def execute_launch57_trust_batch2(launch_item_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if launch_item_id not in LAUNCH57_TRUST_BATCH2_ITEM_IDS:
        raise ValueError(f"launch item {launch_item_id} not in Launch-57 trust batch 2")
    entrypoint = _DISPATCH_BY_LAUNCH_ITEM[launch_item_id]
    fn = globals()[entrypoint]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
