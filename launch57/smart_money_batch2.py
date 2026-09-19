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
from launch57.trust_adaptive_common import (
    apply_inter_entity_internal_flow_filter,
    apply_whale_alert_qualification_filter,
    attach_adaptive_disclosure,
    build_entity_wallet_disclosure,
    build_inter_entity_flow_disclosure,
    build_level1_decision_disclosure,
    build_token_due_diligence_disclosure,
    build_wallet_due_diligence_disclosure,
    build_whale_alert_disclosure,
    compute_approved_token_due_diligence_verdict,
    compute_approved_wallet_due_diligence_verdict,
    derive_entity_wallet_interpretation,
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


def _attach_live_adaptive(
    wrapped: dict[str, Any],
    *,
    p: dict[str, Any],
    launch_item_id: int,
    surface: str,
    answer_state: str,
    disclosure_key: str,
    disclosure: dict[str, Any],
    uncertainty: str = "qualified",
) -> dict[str, Any]:
    wrapped[disclosure_key] = disclosure
    level1 = build_level1_decision_disclosure(
        p,
        launch_item_id=launch_item_id,
        surface=surface,
        answer_state=answer_state,
        evidence_display=wrapped.get("evidence_display"),
        uncertainty=uncertainty,
    )
    return attach_adaptive_disclosure(wrapped, level1, extra={disclosure_key: disclosure})


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
        return attach_smart_money_envelope(body, spine=spine, params=params), None
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
    interpretation = derive_entity_wallet_interpretation(intel)
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
            "entity_interpretation": interpretation,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=14,
        launch_item_id=15,
        entrypoint="entity_aware_wallet_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_entity_wallet_disclosure(interpretation, intel=intel)
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=15,
        surface="entity_aware_wallet_intelligence",
        answer_state=interpretation["answer_state"],
        disclosure_key="entity_wallet_disclosure",
        disclosure=disclosure,
        uncertainty=interpretation["certainty"],
    )


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
    qualified = apply_whale_alert_qualification_filter(
        list(alerts or []),
        derivatives_context=dict(p.get("derivatives_context") or {}),
    )
    alert_worthy = qualified["alert_worthy_alerts"]
    accum = sum(
        1
        for a in alert_worthy
        if "accumulation" in str(a).lower() or a.get("whale_classification", {}).get("class_id") == "possible_accumulation"
    )
    dist = sum(
        1
        for a in alert_worthy
        if "distribution" in str(a).lower() or a.get("whale_classification", {}).get("class_id") == "possible_distribution"
    )
    body = stamp_decision_batch(
        {
            "surface": "whale_accumulation_distribution_intelligence",
            "symbol": spine["symbol"],
            "success": bool(alert_worthy),
            "whale_alerts": alerts,
            "alert_worthy_alerts": alert_worthy,
            "whale_alert_qualification": qualified,
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
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_whale_alert_disclosure(qualified, payload=p)
    answer_state = "ALERT_WORTHY" if alert_worthy else "NO_QUALIFYING_ALERT"
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=18,
        surface="whale_accumulation_distribution_intelligence",
        answer_state=answer_state,
        disclosure_key="whale_alert_disclosure",
        disclosure=disclosure,
    )


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
    symbol_filtered = [
        a
        for a in (alerts or [])
        if spine["symbol"].upper() in str(a).upper()
    ] or alerts
    qualified = apply_whale_alert_qualification_filter(
        list(symbol_filtered or []),
        derivatives_context=dict(p.get("derivatives_context") or {}),
    )
    alert_worthy = qualified["alert_worthy_alerts"]
    body = stamp_decision_batch(
        {
            "surface": "whale_movement_alerts",
            "symbol": spine["symbol"],
            "success": bool(alert_worthy),
            "whale_movement_alerts": symbol_filtered,
            "alert_worthy_alerts": alert_worthy,
            "whale_alert_qualification": qualified,
            "alert_count": len(alert_worthy),
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
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_whale_alert_disclosure(qualified, payload=p)
    answer_state = "ALERT_WORTHY" if alert_worthy else "NO_QUALIFYING_ALERT"
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=18,
        surface="whale_movement_alerts",
        answer_state=answer_state,
        disclosure_key="whale_alert_disclosure",
        disclosure=disclosure,
    )


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
    filtered = apply_inter_entity_internal_flow_filter(ctx, payload=p)
    body = stamp_decision_batch(
        {
            "surface": "inter_entity_flow_intelligence",
            "symbol": spine["symbol"],
            "success": bool(filtered.get("inter_entity_semantics_eligible")),
            "inter_entity_flow": ctx,
            "inter_entity_flow_eligible": filtered.get("inter_entity_flow_eligible"),
            "inter_entity_flow_filter": filtered,
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
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_inter_entity_flow_disclosure(filtered, payload=p)
    answer_state = "INTER_ENTITY_ELIGIBLE" if filtered.get("inter_entity_semantics_eligible") else "INTERNAL_EXCLUDED"
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=19,
        surface="inter_entity_flow_intelligence",
        answer_state=answer_state,
        disclosure_key="inter_entity_flow_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if filtered.get("internal_excluded_count") else "standard",
    )


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
    unapproved_probe = dict(p.get("unapproved_risk_probe") or {})
    approved = compute_approved_wallet_due_diligence_verdict(
        intel=intel,
        surveillance=surveillance,
        spine=spine,
        observable_unapproved=unapproved_probe,
    )

    body = stamp_decision_batch(
        {
            "surface": "instant_wallet_due_diligence",
            "symbol": spine["symbol"],
            "address": address,
            "success": bool(intel.get("ok")),
            "due_diligence": {
                "address_intel": intel,
                "surveillance": surveillance,
                "risk_flags": approved["risk_flags"],
                "verdict": approved["verdict"],
                "approved_verdict": approved,
                "unapproved_observable_only": approved.get("unapproved_observable_only"),
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
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_wallet_due_diligence_disclosure(approved, spine=spine)
    answer_state = str(approved["verdict"]).upper()
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=53,
        surface="instant_wallet_due_diligence",
        answer_state=answer_state,
        disclosure_key="wallet_due_diligence_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if approved["risk_flags"] else "standard",
    )


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
    approved = compute_approved_token_due_diligence_verdict(
        holders=holders,
        financial_models=models,
        spine=spine,
    )
    checklist: dict[str, Any] = {
        "supply_health": holders.get("metrics"),
        "financial_models": models,
        "token": spine["symbol"],
        "risk_flags": approved["risk_flags"],
        "verdict": approved["verdict"],
        "approved_verdict": approved,
        "unapproved_observable_only": approved.get("unapproved_observable_only"),
    }

    body = stamp_decision_batch(
        {
            "surface": "instant_token_due_diligence",
            "symbol": spine["symbol"],
            "success": bool(holders.get("available")),
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
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_token_due_diligence_disclosure(approved, spine=spine)
    answer_state = str(approved["verdict"]).upper()
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=54,
        surface="instant_token_due_diligence",
        answer_state=answer_state,
        disclosure_key="token_due_diligence_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if approved["risk_flags"] else "standard",
    )


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
