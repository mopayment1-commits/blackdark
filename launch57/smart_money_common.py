"""
Launch-57 Phase 4 — shared smart-money spine consuming Phase 1–3 layers.
"""

from __future__ import annotations

from typing import Any

from launch57.decision_common import (
    attach_decision_envelope,
    load_decision_spine,
    require_net_edge_if_cost_claim,
    stale_gate_body,
    stamp_decision_batch,
)

_CAUTIOUS_EXCHANGE_DISCLAIMER = (
    "Cautious risk indicators only — not a solvency certificate, reserve guarantee, "
    "or regulatory fitness attestation. Verify primary sources independently."
)

_MINI_AML_DISCLAIMER = (
    "Suspicious-activity flags on token/smart-money paths only — not a full AML "
    "investigation platform or law-enforcement reporting system."
)

_LIMITED_INTER_ENTITY = (
    "Limited launch scope — inter-entity flow preview without full paid leaderboard."
)


def attach_smart_money_envelope(
    body: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from launch57.b7_market_regime_bridge import finalize_b7_cross_signal_surface
    from launch57.market_regime_timing_common import B7_LAUNCH_NUMBERS

    out = attach_decision_envelope(body, spine=spine)
    out["smart_money_layer"] = {
        "phase": "4_SMART_MONEY_INSTANT",
        "data_spine_consumed": (spine or {}).get("data_spine"),
        "freshness_state": (spine or {}).get("freshness_state"),
        "live_eligible": (spine or {}).get("live_eligible"),
        "evidence_class_visible": out.get("evidence_class_visible"),
    }
    launch_id = int(out.get("launch_item_id") or 0)
    if launch_id in B7_LAUNCH_NUMBERS:
        out = finalize_b7_cross_signal_surface(
            out,
            payload=dict(params or {}),
            spine=spine,
            fail_closed_on_mismatch=out.get("success") is not False,
        )
    from launch57.b12_due_diligence_risk_bridge import finalize_b12_due_diligence_risk_surface
    from launch57.due_diligence_risk_timing_common import B12_LAUNCH_NUMBERS

    if launch_id in B12_LAUNCH_NUMBERS:
        p = dict(params or {})
        out = finalize_b12_due_diligence_risk_surface(
            out,
            payload=p,
            spine=spine,
            display_timezone=p.get("display_timezone"),
        )
    from launch57.infrastructure_boundary_common import attach_infrastructure_boundary

    return attach_infrastructure_boundary(out, params=dict(params or {}))


def cautious_exchange_footer() -> dict[str, str]:
    return {
        "disclaimer": _CAUTIOUS_EXCHANGE_DISCLAIMER,
        "solvency_certificate_claim": "FORBIDDEN",
        "reserve_guarantee_claim": "FORBIDDEN",
        "indicators_only": True,
    }


def mini_aml_footer() -> dict[str, str]:
    return {
        "disclaimer": _MINI_AML_DISCLAIMER,
        "full_aml_platform": False,
        "scope": "token_smart_money_paths_only",
    }


def limited_inter_entity_footer() -> dict[str, str]:
    return {
        "disclaimer": _LIMITED_INTER_ENTITY,
        "paid_leaderboard_full": False,
        "limited_launch_scope": True,
    }
