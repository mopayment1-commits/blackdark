"""
Launch-57 Phase 4 — Smart Money Batch 2.

Build order: #15 CAP-0014 → #18 CAP-0081/0098 → #19 CAP-0091 → #53 CAP-0022 → #54 CAP-0023
"""

from __future__ import annotations

from typing import Any

from launch57.smart_money_common import (
    attach_smart_money_envelope,
    limited_inter_entity_footer,
    load_decision_spine,
    stale_gate_body,
    stamp_decision_batch,
)

LAUNCH57_SMART_MONEY_BATCH2_CAP_IDS: frozenset[int] = frozenset({14, 81, 98, 91, 22, 23})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    14: 15,
    81: 18,
    98: 18,
    91: 19,
    22: 53,
    23: 54,
}

_BINDING = "launch57_phase4_smart_money_batch2"
_MODULE = "launch57.smart_money_batch2"


async def _gated(
    *,
    capability_id: int,
    launch_item_id: int,
    surface: str,
    entrypoint: str,
    symbol: str,
    params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    spine = await load_decision_spine(symbol, params)
    if not spine["live_eligible"]:
        body = stamp_decision_batch(
            stale_gate_body(
                capability_id=capability_id,
                launch_item_id=launch_item_id,
                surface=surface,
                symbol=spine["symbol"],
                spine=spine,
                entrypoint=entrypoint,
            ),
            capability_id=capability_id,
            launch_item_id=launch_item_id,
            entrypoint=entrypoint,
            batch_module=_MODULE,
            binding_source=_BINDING,
        )
        return attach_smart_money_envelope(body, spine=spine), None
    return None, spine


async def entity_aware_wallet_intelligence(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #15 / CAP-0014 — entity-aware wallet intelligence."""
    from bd_platform.address_intelligence import search_address

    p = dict(params or {})
    address = str(p.get("address") or "0x0000000000000000000000000000000000000000")
    blocked, spine = await _gated(
        capability_id=14,
        launch_item_id=15,
        surface="entity_aware_wallet_intelligence",
        entrypoint="entity_aware_wallet_intelligence",
        symbol=symbol,
        params={**p, "address": address},
    )
    if blocked:
        return blocked

    intel = await search_address(address, chain=str(p.get("chain") or "ethereum"))
    body = stamp_decision_batch(
        {
            "surface": "entity_aware_wallet_intelligence",
            "symbol": spine["symbol"],
            "address": address,
            "success": bool(intel.get("ok")),
            "entity_label": intel.get("entity_label"),
            "labels": intel.get("labels"),
            "clusters": intel.get("clusters"),
            "arkham_entity": intel.get("arkham_entity"),
            "total_usd": intel.get("total_usd"),
            "data_state": intel.get("data_state"),
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=14,
        launch_item_id=15,
        entrypoint="entity_aware_wallet_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


async def whale_accumulation_distribution_intelligence(
    *, symbol: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Launch #18 / CAP-0081 — whale accumulation / distribution alerts."""
    from whale_tracker import get_latest_whale_alerts

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=81,
        launch_item_id=18,
        surface="whale_accumulation_distribution_intelligence",
        entrypoint="whale_accumulation_distribution_intelligence",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    alerts = await get_latest_whale_alerts(limit=int(p.get("limit") or 20))
    accum = sum(1 for a in (alerts or []) if "accumulation" in str(a).lower())
    dist = sum(1 for a in (alerts or []) if "distribution" in str(a).lower())
    body = stamp_decision_batch(
        {
            "surface": "whale_accumulation_distribution_intelligence",
            "symbol": spine["symbol"],
            "success": bool(alerts),
            "whale_alerts": alerts,
            "accumulation_signals": accum,
            "distribution_signals": dist,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=81,
        launch_item_id=18,
        entrypoint="whale_accumulation_distribution_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


async def whale_movement_alerts(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #18 / CAP-0098 — whale movement alerts."""
    from whale_tracker import get_latest_whale_alerts

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=98,
        launch_item_id=18,
        surface="whale_movement_alerts",
        entrypoint="whale_movement_alerts",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    alerts = await get_latest_whale_alerts(limit=int(p.get("limit") or 25))
    filtered = [
        a
        for a in (alerts or [])
        if spine["symbol"].upper() in str(a).upper()
    ] or alerts
    body = stamp_decision_batch(
        {
            "surface": "whale_movement_alerts",
            "symbol": spine["symbol"],
            "success": bool(filtered),
            "whale_movement_alerts": filtered,
            "alert_count": len(filtered or []),
            "alias_launch_item": 18,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=98,
        launch_item_id=18,
        entrypoint="whale_movement_alerts",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


async def inter_entity_flow_intelligence(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #19 / CAP-0091 — inter-entity flow (limited launch scope)."""
    from onchain_tracker import build_onchain_context_safe

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=91,
        launch_item_id=19,
        surface="inter_entity_flow_intelligence",
        entrypoint="inter_entity_flow_intelligence",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    ctx = await build_onchain_context_safe()
    body = stamp_decision_batch(
        {
            "surface": "inter_entity_flow_intelligence",
            "symbol": spine["symbol"],
            "success": bool(ctx),
            "inter_entity_flow": ctx,
            "entity_routing": True,
            "limited_launch_scope": limited_inter_entity_footer(),
            "paid_leaderboard_full": False,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=91,
        launch_item_id=19,
        entrypoint="inter_entity_flow_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


async def instant_wallet_due_diligence(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #53 / CAP-0022 — instant wallet due diligence."""
    from bd_platform.address_intelligence import search_address
    from bd_platform.whales_institutional_layer import analyze_wallet_surveillance_79

    p = dict(params or {})
    address = str(p.get("address") or "0x0000000000000000000000000000000000000000")
    blocked, spine = await _gated(
        capability_id=22,
        launch_item_id=53,
        surface="instant_wallet_due_diligence",
        entrypoint="instant_wallet_due_diligence",
        symbol=symbol,
        params={**p, "address": address},
    )
    if blocked:
        return blocked

    intel = await search_address(address, chain=str(p.get("chain") or "ethereum"))
    surveillance = analyze_wallet_surveillance_79(wallet=address)
    risk_flags: list[str] = []
    if not intel.get("ok"):
        risk_flags.append("address_lookup_failed")
    if surveillance.get("surveillance_detected"):
        risk_flags.append("elevated_surveillance_pattern")

    body = stamp_decision_batch(
        {
            "surface": "instant_wallet_due_diligence",
            "symbol": spine["symbol"],
            "address": address,
            "success": bool(intel.get("ok")),
            "due_diligence": {
                "address_intel": intel,
                "surveillance": surveillance,
                "risk_flags": risk_flags,
                "verdict": "review" if risk_flags else "clear",
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=22,
        launch_item_id=53,
        entrypoint="instant_wallet_due_diligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


async def instant_token_due_diligence(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #54 / CAP-0023 — instant token due diligence."""
    from bd_platform.free_integrations import holder_analytics
    from research_lab import compute_financial_models

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=23,
        launch_item_id=54,
        surface="instant_token_due_diligence",
        entrypoint="instant_token_due_diligence",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    holders = await holder_analytics(spine["symbol"])
    models = await compute_financial_models(spine["symbol"], notional=float(p.get("notional") or 10_000))
    checklist: dict[str, Any] = {
        "supply_health": holders.get("metrics"),
        "financial_models": models,
        "token": spine["symbol"],
        "risk_flags": [],
    }
    locked = float((holders.get("metrics") or {}).get("locked_supply_pct") or 0)
    if locked > 70:
        checklist["risk_flags"].append("high_locked_supply")
    if models.get("error"):
        checklist["risk_flags"].append("financial_model_gap")

    body = stamp_decision_batch(
        {
            "surface": "instant_token_due_diligence",
            "symbol": spine["symbol"],
            "success": bool(holders.get("available") or not models.get("error")),
            "token_due_diligence": checklist,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=23,
        launch_item_id=54,
        entrypoint="instant_token_due_diligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


_DISPATCH: dict[int, str] = {
    14: "entity_aware_wallet_intelligence",
    81: "whale_accumulation_distribution_intelligence",
    98: "whale_movement_alerts",
    91: "inter_entity_flow_intelligence",
    22: "instant_wallet_due_diligence",
    23: "instant_token_due_diligence",
}


async def execute_launch57_smart_money_batch2(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_SMART_MONEY_BATCH2_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 smart money batch 2")
    fn = globals()[_DISPATCH[capability_id]]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
