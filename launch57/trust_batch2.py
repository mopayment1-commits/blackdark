"""
Launch-57 Phase 2 — Trust Batch 2 product surfaces.

Build order: #47 risk disclosure → #48 abstain/reject → #44 share card → #45 accuracy page → #46 guest trust
"""

from __future__ import annotations

from typing import Any

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

    body = {
        "launch_item_id": 47,
        "surface": "one_click_risk_disclosure",
        "symbol": symbol,
        "success": True,
        "risk_disclosure": {
            "compliance_footer": compliance,
            "reject_proof": reject_proof,
            "material_claims": product.get("material_claims"),
            "one_click": True,
            "derived_from": "canonical_govern_pipeline",
        },
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "one_click_risk_disclosure",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    return attach_trust_envelope(body)


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

    body = {
        "launch_item_id": 48,
        "surface": "abstain_reject_reasons_visible",
        "symbol": symbol,
        "success": True,
        "no_decision": no_decision,
        "rejection_engine": rejection,
        "reasons_visible": True,
        "hidden_as_error": bool(no_decision.get("hidden_as_error")),
        "first_class_abstain": bool(no_decision.get("first_class_state")),
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "abstain_reject_reasons_visible",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    return attach_trust_envelope(body)


async def shareable_decision_card(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #44 — shareable decision/oracle card (OG metadata)."""
    from decision_certificate import build_decision_certificate

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
        "alias_of": "CAP-0641",
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "shareable_decision_card",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    return _finalize_trust_batch2_surface(body, params=p)


async def shareable_accuracy_page(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #45 — shareable accuracy/outcome page (alias of CAP-0640 live ledger)."""
    from oracle_track_record import public_track_record

    p = dict(params or {})
    ledger = public_track_record()
    cumulative = ledger.get("cumulative") or {}
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
        "ledger": ledger,
        "alias_of": "CAP-0640",
        "live_only_primary": True,
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "shareable_accuracy_page",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    return _finalize_trust_batch2_surface(body, params=p)


async def guest_trust_surface(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #46 — guest/anonymous trust surface."""
    from governance.anonymous_visitor_governance import anonymous_visitor_status

    p = dict(params or {})
    status = anonymous_visitor_status()
    body = {
        "launch_item_id": 46,
        "surface": "guest_trust_surface",
        "symbol": symbol,
        "success": True,
        "guest_trust": {
            "anonymous_state": status.get("anonymous_state"),
            "private_by_default": status.get("private_by_default"),
            "public_readiness": status.get("public_readiness"),
            "rate_limits": status.get("rate_limits"),
            "no_pii_leak": status.get("no_pii_leak"),
            "visitor_tier_gating": status.get("visitor_tier_gating"),
            "route_inventory": status.get("route_inventory"),
        },
        "backend_module": "launch57.trust_batch2",
        "backend_entrypoint": "guest_trust_surface",
        "binding_source": "launch57_phase2_trust_batch2",
    }
    return _finalize_trust_batch2_surface(body, params=p)


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
