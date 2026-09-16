"""
Launch-57 Phase 3 — Decision Batch 2 canonical runtime spine.

Build order: #12 CAP-0028 → #37 CAP-0029
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

LAUNCH57_DECISION_BATCH2_CAP_IDS: frozenset[int] = frozenset({28, 29})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    28: 12,
    29: 37,
}

_BINDING = "launch57_phase3_decision_batch2"
_MODULE = "launch57.decision_batch2"


async def smart_money_conviction_engine(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #12 / CAP-0028 — Smart Money Conviction Engine."""
    from bd_platform.retail_intelligence_layer import evaluate_contextual_alert_65

    p = dict(params or {})
    spine = await load_decision_spine(symbol, p)
    if not spine["live_eligible"]:
        return attach_decision_envelope(
            stamp_decision_batch(
                stale_gate_body(
                    capability_id=28,
                    launch_item_id=12,
                    surface="smart_money_conviction_engine",
                    symbol=spine["symbol"],
                    spine=spine,
                    entrypoint="smart_money_conviction_engine",
                ),
                capability_id=28,
                launch_item_id=12,
                entrypoint="smart_money_conviction_engine",
                batch_module=_MODULE,
                binding_source=_BINDING,
            ),
            spine=spine,
        )

    price = float(spine.get("price") or 0)
    if price <= 0:
        body = stamp_decision_batch(
            {
                "surface": "smart_money_conviction_engine",
                "symbol": spine["symbol"],
                "success": False,
                "error": "price_unavailable_for_conviction",
                "presented_as_live": False,
            },
            capability_id=28,
            launch_item_id=12,
            entrypoint="smart_money_conviction_engine",
            batch_module=_MODULE,
            binding_source=_BINDING,
        )
        return attach_decision_envelope(body, spine=spine)

    alert = evaluate_contextual_alert_65(
        user_tier=str(p.get("tier") or "pro"),
        price=price,
        opportunity_level=float(p.get("opportunity_level") or 7.5),
        volume_zscore=float(p.get("volume_zscore") or 2.0),
        asset=spine["symbol"],
    )
    conviction = 0.0
    if alert.get("alert_fired"):
        conviction = min(100.0, float(p.get("opportunity_level") or 7.5) * 10)

    body = stamp_decision_batch(
        {
            "surface": "smart_money_conviction_engine",
            "symbol": spine["symbol"],
            "success": conviction > 0 or bool(alert),
            "conviction_score": conviction,
            "alert": alert,
            "price_source": "launch57.data_batch1",
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=28,
        launch_item_id=12,
        entrypoint="smart_money_conviction_engine",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_decision_envelope(body, spine=spine)


async def cross_market_decision_engine(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #37 / CAP-0029 — Cross-market decision engine."""
    from bd_platform.institutional_delivery_intelligence_layer import cross_market_decision_intelligence_567
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73

    p = dict(params or {})
    spine = await load_decision_spine(symbol, p)
    if not spine["live_eligible"]:
        return attach_decision_envelope(
            stamp_decision_batch(
                stale_gate_body(
                    capability_id=29,
                    launch_item_id=37,
                    surface="cross_market_decision_intelligence_engine",
                    symbol=spine["symbol"],
                    spine=spine,
                    entrypoint="cross_market_decision_engine",
                ),
                capability_id=29,
                launch_item_id=37,
                entrypoint="cross_market_decision_engine",
                batch_module=_MODULE,
                binding_source=_BINDING,
            ),
            spine=spine,
        )

    cost_claim = bool(p.get("cost_claim") or p.get("opportunity"))
    net_edge_gate = await require_net_edge_if_cost_claim(
        symbol=spine["symbol"],
        params=p,
        cost_claim=cost_claim,
    )
    if net_edge_gate and net_edge_gate.get("blocked"):
        body = stamp_decision_batch(
            {
                "surface": "cross_market_decision_intelligence_engine",
                "symbol": spine["symbol"],
                "success": False,
                "error": net_edge_gate.get("reason"),
                "net_edge_gate": net_edge_gate,
                "decision_engine": None,
                "cost_claim_blocked": True,
                "presented_as_live": False,
            },
            capability_id=29,
            launch_item_id=37,
            entrypoint="cross_market_decision_engine",
            batch_module=_MODULE,
            binding_source=_BINDING,
        )
        return attach_decision_envelope(body, spine=spine)

    multi_dim = build_multi_dim_analysis_73(asset=spine["symbol"])
    cross = cross_market_decision_intelligence_567(symbol=spine["symbol"])
    body = stamp_decision_batch(
        {
            "surface": "cross_market_decision_intelligence_engine",
            "symbol": spine["symbol"],
            "success": bool(multi_dim.get("ok", True)),
            "decision_engine": {
                "multi_dimensional": multi_dim,
                "cross_market": cross,
                "composite_score": multi_dim.get("composite_score"),
                "spot_derivatives_flow": True,
            },
            "net_edge_gate": net_edge_gate,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
            "data_spine_ref": spine["data_spine"],
        },
        capability_id=29,
        launch_item_id=37,
        entrypoint="cross_market_decision_engine",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_decision_envelope(body, spine=spine)


_DISPATCH_ENTRYPOINTS: dict[int, str] = {
    28: "smart_money_conviction_engine",
    29: "cross_market_decision_engine",
}


async def execute_launch57_decision_batch2(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_DECISION_BATCH2_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 decision batch 2")
    entrypoint = _DISPATCH_ENTRYPOINTS[capability_id]
    fn = globals()[entrypoint]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
