"""
Launch-57 Phase 3 — shared decision spine consuming Phase 1 data + Phase 2 trust.
"""

from __future__ import annotations

from typing import Any

from failure.freshness import FreshnessState
from launch57.trust_batch1 import attach_trust_envelope

_LIVE_ELIGIBLE = frozenset(
    {
        FreshnessState.LIVE.value,
        FreshnessState.NEAR_LIVE.value,
        FreshnessState.DELAYED.value,
    }
)


async def load_decision_spine(symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Consume Phase 1 launch57 data layers — no parallel price path for decisions."""
    from launch57.data_batch1 import real_time_prices
    from launch57.data_batch2 import freshness_update_assurance

    p = dict(params or {})
    asset = str(p.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")

    prices = await real_time_prices(symbol=asset, params=p)
    freshness = await freshness_update_assurance(symbol=asset, params=p)

    freshness_state = str(
        prices.get("freshness_state")
        or freshness.get("freshness_state")
        or FreshnessState.UNKNOWN.value
    )
    live_eligible = freshness_state in _LIVE_ELIGIBLE and bool(prices.get("presented_as_live"))

    return {
        "symbol": asset,
        "prices": prices,
        "freshness": freshness,
        "freshness_state": freshness_state,
        "live_eligible": live_eligible,
        "presented_as_live": live_eligible,
        "price": prices.get("price"),
        "change_24h": prices.get("change_24h"),
        "data_spine": {
            "phase1_batch1": "launch57.data_batch1:real_time_prices",
            "phase1_batch2": "launch57.data_batch2:freshness_update_assurance",
        },
    }


def stale_gate_body(
    *,
    capability_id: int,
    launch_item_id: int,
    surface: str,
    symbol: str,
    spine: dict[str, Any],
    entrypoint: str,
) -> dict[str, Any]:
    from launch57.decision_truth_common import attach_decision_truth_envelope
    from launch57.failure_recovery_common import attach_failure_recovery_envelope

    body = {
        "capability_id": capability_id,
        "launch_item_id": launch_item_id,
        "surface": surface,
        "symbol": symbol,
        "success": False,
        "error": "decision_blocked_stale_or_unknown_data",
        "freshness_state": spine.get("freshness_state"),
        "presented_as_live": False,
        "decision_live_blocked": True,
        "policy": "no_live_decision_on_stale_or_unknown",
        "data_spine": spine.get("data_spine"),
        "backend_module": "launch57.decision_common",
        "backend_entrypoint": entrypoint,
        "binding_source": "launch57_phase3_decision_spine",
    }
    from launch57.compounding_evidence_common import attach_compounding_evidence_envelope
    from launch57.teis_support_common import attach_teis_support_envelope

    body = attach_teis_support_envelope(body)
    body = attach_failure_recovery_envelope(body, launch_item_id=launch_item_id)
    body = attach_decision_truth_envelope(body, launch_item_id=launch_item_id)
    return attach_compounding_evidence_envelope(body, launch_item_id=launch_item_id)


async def require_net_edge_if_cost_claim(
    *,
    symbol: str,
    params: dict[str, Any],
    cost_claim: bool,
) -> dict[str, Any] | None:
    """Phase 2 #5 — block cost/edge claims without Net-Edge path."""
    if not cost_claim:
        return None
    from launch57.trust_batch1 import net_edge_truth_score

    opportunity = params.get("opportunity")
    if not opportunity:
        return {
            "blocked": True,
            "reason": "cost_claim_requires_opportunity_and_net_edge",
            "net_edge_path": "launch57.trust_batch1:net_edge_truth_score",
        }
    edge = await net_edge_truth_score(symbol=symbol, params={"opportunity": opportunity})
    if not edge.get("success") or not edge.get("cost_claim_allowed"):
        return {
            "blocked": True,
            "reason": edge.get("error") or "net_edge_not_passing",
            "net_edge": edge.get("net_edge_truth_score"),
            "net_edge_path": "launch57.trust_batch1:net_edge_truth_score",
        }
    return {"blocked": False, "net_edge": edge.get("net_edge_truth_score")}


def attach_decision_envelope(body: dict[str, Any], *, spine: dict[str, Any] | None = None) -> dict[str, Any]:
    from launch57.failure_recovery_common import attach_failure_recovery_envelope

    out = attach_trust_envelope(dict(body))
    out["decision_layer"] = {
        "phase": "3_DECISION",
        "data_spine_consumed": (spine or {}).get("data_spine"),
        "freshness_state": (spine or {}).get("freshness_state"),
        "live_eligible": (spine or {}).get("live_eligible"),
        "evidence_class_visible": out.get("evidence_class_visible"),
    }
    launch_id = int(out.get("launch_item_id") or 0)
    from launch57.decision_truth_common import attach_decision_truth_envelope

    from launch57.compounding_evidence_common import attach_compounding_evidence_envelope
    from launch57.teis_support_common import attach_teis_support_envelope

    out = attach_teis_support_envelope(out)
    out = attach_failure_recovery_envelope(out, launch_item_id=launch_id or None)
    out = attach_decision_truth_envelope(out, launch_item_id=launch_id or None)
    return attach_compounding_evidence_envelope(out, launch_item_id=launch_id or None)


def stamp_decision_batch(
    body: dict[str, Any],
    *,
    capability_id: int,
    launch_item_id: int,
    entrypoint: str,
    batch_module: str,
    binding_source: str,
) -> dict[str, Any]:
    out = dict(body)
    out.setdefault("capability_id", capability_id)
    out.setdefault("launch_item_id", launch_item_id)
    out["backend_module"] = batch_module
    out["backend_entrypoint"] = entrypoint
    out["binding_source"] = binding_source
    return out
