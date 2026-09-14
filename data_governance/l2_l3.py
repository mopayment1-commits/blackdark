"""L2/L3 selective policy — L2 mandatory for execution-sensitive; L3 selective."""

from __future__ import annotations

from typing import Any

FEATURE_L2_REQUIREMENTS: dict[str, bool] = {
    "expected_slippage": True,
    "execution_feasibility": True,
    "liquidity_capacity": True,
    "depth_imbalance": True,
    "realizable_net_edge": True,
    "net_edge": False,
    "ticker_monitoring": False,
}

FEATURE_L3_REQUIREMENTS: dict[str, bool] = {
    "queue_position": True,
    "order_identity": True,
    "net_edge": False,
    "execution_feasibility": False,
}


def l2_required_for(feature: str) -> bool:
    return FEATURE_L2_REQUIREMENTS.get(feature, False)


def l3_required_for(feature: str) -> bool:
    return FEATURE_L3_REQUIREMENTS.get(feature, False)


def evaluate_depth_sufficiency(*, feature: str, has_l1: bool, has_l2: bool, has_l3: bool) -> dict[str, Any]:
    l2_req = l2_required_for(feature)
    l3_req = l3_required_for(feature)
    ok = has_l1 and (not l2_req or has_l2) and (not l3_req or has_l3)
    return {
        "feature": feature,
        "l2_required": l2_req,
        "l3_required": l3_req,
        "has_l1": has_l1,
        "has_l2": has_l2,
        "has_l3": has_l3,
        "sufficient": ok,
        "false_l3_claim": has_l3 and not l3_req,
    }


def attach_l2_l3_policy(payload: dict[str, Any], *, feature: str = "execution_feasibility") -> dict[str, Any]:
    out = dict(payload)
    has_l1 = bool(out.get("quote_age_ms") is not None or out.get("mid_price"))
    has_l2 = bool(out.get("depth_usd") or out.get("l2_available"))
    has_l3 = bool(out.get("l3_available"))
    out["l2_l3_policy"] = evaluate_depth_sufficiency(feature=feature, has_l1=has_l1, has_l2=has_l2, has_l3=has_l3)
    return out
