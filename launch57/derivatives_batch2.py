"""
Launch-57 Phase 5 — Derivatives + Habits Batch 2.

Build order: #30 CAP-0050/0508 → #31 CAP-0056 → #32 CAP-0019 → #33 CAP-0017
"""

from __future__ import annotations

from typing import Any

from launch57.decision_common import load_decision_spine, stale_gate_body, stamp_decision_batch
from launch57.derivatives_common import (
    attach_derivatives_envelope,
    l1_order_book_footer,
    limited_watchlist_footer,
    smart_alerts_external_status,
)
from launch57.trust_adaptive_common import (
    apply_general_market_screener_guard,
    apply_limited_watchlist_guard,
    apply_order_book_intelligence_semantics,
    apply_smart_alerts_qualification_filter,
    attach_adaptive_disclosure,
    build_general_market_screener_disclosure,
    build_level1_decision_disclosure,
    build_limited_watchlist_disclosure,
    build_order_book_intelligence_disclosure,
    build_smart_alerts_disclosure,
)

LAUNCH57_DERIVATIVES_BATCH2_CAP_IDS: frozenset[int] = frozenset({50, 508, 56, 19, 17})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    50: 30,
    508: 30,
    56: 31,
    19: 32,
    17: 33,
}

_BINDING = "launch57_phase5_derivatives_batch2"
_MODULE = "launch57.derivatives_batch2"


def _governed_params(p: dict[str, Any], semantics: dict[str, Any], spine: dict[str, Any]) -> dict[str, Any]:
    out = dict(p)
    governed = dict(out.get("governed_payload") or {})
    contract = semantics.get("contract") or {}
    if contract.get("material_contradiction"):
        governed["critical_contradiction"] = contract["material_contradiction"]
    limitation = contract.get("material_limitation") or semantics.get("material_limitation")
    if limitation:
        governed["critical_limitation"] = limitation
    if semantics.get("material_disagreements"):
        governed["contradictions"] = semantics["material_disagreements"]
    out["governed_payload"] = governed
    out["freshness_state"] = spine.get("freshness_state")
    return out


def _attach_habits_adaptive(
    wrapped: dict[str, Any],
    *,
    p: dict[str, Any],
    spine: dict[str, Any],
    launch_item_id: int,
    surface: str,
    semantics: dict[str, Any],
    disclosure_key: str,
    disclosure: dict[str, Any],
) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    if contract:
        wrapped["derivatives_contract"] = contract
        wrapped["evidence_class_visible"] = contract.get("evidence_class")
    wrapped["evidence_display"] = {
        "canonical_evidence_class": contract.get("evidence_class") or semantics.get("market_scope"),
        "freshness_state": spine.get("freshness_state"),
    }
    governed_p = _governed_params(p, semantics, spine)
    uncertainty = "qualified" if contract.get("material_contradiction") or semantics.get("scope_rejected") or semantics.get("domain_rejected") else "standard"
    level1 = build_level1_decision_disclosure(
        governed_p,
        launch_item_id=launch_item_id,
        surface=surface,
        answer_state=semantics.get("answer_state"),
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
        return attach_derivatives_envelope(body, spine=spine, params=params), None
    return None, spine


async def order_book_intelligence(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #30 / CAP-0050 — order book intelligence (L1 minimum)."""
    from cap646.fallbacks import resolve_order_book
    from live_book_hub import hub_stats

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=50,
        launch_item_id=30,
        surface="order_book_intelligence",
        entrypoint="order_book_intelligence",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    book = await resolve_order_book(spine["symbol"])
    depth = l1_order_book_footer(depth_level="L1")
    semantics = apply_order_book_intelligence_semantics(book=book, spine=spine, depth_level="L1")
    body = stamp_decision_batch(
        {
            "surface": "order_book_intelligence",
            "symbol": spine["symbol"],
            "success": bool(semantics.get("book_observable")),
            "book": book,
            "hub_stats": hub_stats(),
            "order_book_depth": depth,
            "depth_level": "L1",
            "deeper_than_l1": False,
            "book_direction": semantics.get("book_direction"),
            "order_book_semantics": semantics,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=50,
        launch_item_id=30,
        entrypoint="order_book_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_order_book_intelligence_disclosure(semantics)
    return _attach_habits_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=30,
        surface="order_book_intelligence",
        semantics=semantics,
        disclosure_key="order_book_intelligence_disclosure",
        disclosure=disclosure,
    )


async def l1_order_book_layer(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #30 / CAP-0508 — explicit L1 order book layer."""
    from cap646.fallbacks import resolve_order_book

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=508,
        launch_item_id=30,
        surface="l1_order_book",
        entrypoint="l1_order_book_layer",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    book = await resolve_order_book(spine["symbol"])
    depth = l1_order_book_footer(depth_level="L1")
    semantics = apply_order_book_intelligence_semantics(book=book, spine=spine, depth_level="L1")
    body = stamp_decision_batch(
        {
            "surface": "l1_order_book",
            "symbol": spine["symbol"],
            "success": bool(semantics.get("book_observable")),
            "l1_order_book": book,
            "order_book_depth": depth,
            "book_direction": semantics.get("book_direction"),
            "order_book_semantics": semantics,
            "alias_launch_item": 30,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=508,
        launch_item_id=30,
        entrypoint="l1_order_book_layer",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_order_book_intelligence_disclosure(semantics)
    return _attach_habits_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=30,
        surface="l1_order_book",
        semantics=semantics,
        disclosure_key="order_book_intelligence_disclosure",
        disclosure=disclosure,
    )


async def general_market_token_screener(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #31 / CAP-0056 — general market token screener."""
    from bd_platform.market_rankings import market_rankings

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=56,
        launch_item_id=31,
        surface="token_screener",
        entrypoint="general_market_token_screener",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    rankings = await market_rankings()
    rows = rankings.get("rankings") or rankings.get("markets") or rankings
    if isinstance(rows, list) and spine["symbol"] != "BTC":
        filtered = [r for r in rows if str(r.get("symbol") or "").upper() == spine["symbol"]]
        screener = filtered or rows[:25]
    else:
        screener = rows[:25] if isinstance(rows, list) else rows

    guarded = apply_general_market_screener_guard(screener, params=p, spine=spine)
    body = stamp_decision_batch(
        {
            "surface": "token_screener",
            "symbol": spine["symbol"],
            "success": guarded.get("answer_state") == "GENERAL_MARKET_SCREENED",
            "screener": guarded.get("screener_rows"),
            "screener_guard": guarded,
            "market_scope": guarded.get("market_scope"),
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=56,
        launch_item_id=31,
        entrypoint="general_market_token_screener",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_general_market_screener_disclosure(guarded)
    return _attach_habits_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=31,
        surface="token_screener",
        semantics=guarded,
        disclosure_key="general_market_screener_disclosure",
        disclosure=disclosure,
    )


async def limited_watchlists(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #32 / CAP-0019 — limited token + wallet watchlists."""
    from bd_platform.security_trust_data_layer import list_etherscan_watchlist_246

    p = dict(params or {})
    address = str(p.get("address") or "")
    blocked, spine = await _gated(
        capability_id=19,
        launch_item_id=32,
        surface="wallet_token_watchlists",
        entrypoint="limited_watchlists",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    watches = list_etherscan_watchlist_246()
    wallet_watches = watches.get("watches") or []
    guarded = apply_limited_watchlist_guard(
        wallet_watches[: int(p.get("limit") or 25)],
        params=p,
        spine=spine,
    )
    body = stamp_decision_batch(
        {
            "surface": "wallet_token_watchlists",
            "symbol": spine["symbol"],
            "success": guarded.get("answer_state") == "WATCHLIST_OBSERVABLE",
            "wallet_watchlists": guarded.get("wallet_watchlists"),
            "watchlist_guard": guarded,
            "token_filter": spine["symbol"],
            "address_context": address or None,
            "limited_watchlist_scope": limited_watchlist_footer(),
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=19,
        launch_item_id=32,
        entrypoint="limited_watchlists",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_limited_watchlist_disclosure(guarded)
    from launch57.identity_auth_common import attach_identity_auth_envelope

    adapted = _attach_habits_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=32,
        surface="wallet_token_watchlists",
        semantics=guarded,
        disclosure_key="limited_watchlist_disclosure",
        disclosure=disclosure,
    )
    from launch57.billing_entitlement_common import attach_billing_entitlement_envelope

    adapted = attach_identity_auth_envelope(
        adapted,
        launch_item_id=32,
        surface_type="private",
        params=p,
    )
    return attach_billing_entitlement_envelope(adapted, launch_item_id=32, params=p)


async def smart_alerts_composite(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #33 / CAP-0017 — smart alerts: price + flow + whale + decision."""
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75
    from bd_platform.retail_intelligence_layer import evaluate_contextual_alert_65
    from cap646.dedicated_common import exchange_netflow_probe
    from instant_alert_engine import engine_stats
    from whale_tracker import get_latest_whale_alerts

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=17,
        launch_item_id=33,
        surface="smart_alerts",
        entrypoint="smart_alerts_composite",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    price = float(spine.get("price") or 0)
    change = float(spine.get("change_24h") or 0)
    exchange, netflow = exchange_netflow_probe(p, spine["symbol"])
    net = float(netflow.get("netflow_usd") or netflow.get("net") or 0)
    whale_alerts = await get_latest_whale_alerts(limit=int(p.get("limit") or 10))
    whale_hits = [a for a in (whale_alerts or []) if spine["symbol"].upper() in str(a).upper()]

    price_trigger = {
        "rule": f"price_move:{spine['symbol']}",
        "metric": "change_24h_pct",
        "value": change,
        "threshold": float(p.get("price_threshold_pct") or 3.0),
    }
    flow_trigger = {
        "rule": f"exchange_flow:{exchange}",
        "metric": "netflow_usd",
        "value": net,
        "threshold": float(p.get("flow_threshold_usd") or 1_000_000),
    }
    whale_trigger = {
        "rule": f"whale_activity:{spine['symbol']}",
        "metric": "whale_alert_count",
        "value": len(whale_hits),
        "threshold": float(p.get("whale_threshold") or 1),
    }
    decision_alert = evaluate_contextual_alert_65(
        user_tier=str(p.get("tier") or "pro"),
        price=price,
        opportunity_level=float(p.get("opportunity_level") or 6.0),
        volume_zscore=float(p.get("volume_zscore") or 1.5),
        asset=spine["symbol"],
    ) if price > 0 else {"alert_fired": False, "reason": "price_unavailable"}

    evaluations = {
        "price": evaluate_flexible_alert_75(user_tier=str(p.get("tier") or "pro"), trigger=price_trigger),
        "flow": evaluate_flexible_alert_75(user_tier=str(p.get("tier") or "pro"), trigger=flow_trigger),
        "whale": evaluate_flexible_alert_75(user_tier=str(p.get("tier") or "pro"), trigger=whale_trigger),
        "decision": decision_alert,
    }
    triggers = {
        "price": price_trigger,
        "flow": flow_trigger,
        "whale": whale_trigger,
    }
    filtered = apply_smart_alerts_qualification_filter(
        evaluations,
        triggers=triggers,
        params=p,
        spine=spine,
        symbol=spine["symbol"],
    )
    fired = list(filtered.get("fired_channels") or [])
    qualified_evaluations = filtered.get("qualified_evaluations") or {}
    external = smart_alerts_external_status()
    delivery = external["delivery_status"]
    local_ok = bool(fired) and filtered.get("answer_state") == "ALERTS_FIRED"

    body = stamp_decision_batch(
        {
            "surface": "smart_alerts",
            "symbol": spine["symbol"],
            "success": local_ok,
            "smart_alerts": {
                "triggers": triggers,
                "evaluations": qualified_evaluations,
                "raw_evaluations": evaluations,
                "fired_channels": fired,
                "engine": engine_stats(),
                "alert_qualification": filtered,
            },
            "delivery_status": delivery,
            "external_delivery": external,
            "presented_as_live": spine["presented_as_live"] and not filtered.get("delayed_not_presented_as_live"),
            "local_alert_path": "launch57.derivatives_batch2:smart_alerts_composite",
            "freshness_state": spine["freshness_state"],
        },
        capability_id=17,
        launch_item_id=33,
        entrypoint="smart_alerts_composite",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    if delivery == "BLOCKED_EXTERNAL":
        body["blocked_external"] = True
        body["blocked_external_reason"] = external.get("blocked_reason")
        body["external_push_live"] = False
    from launch57.b8_alerts_bridge import finalize_b8_alert_surface

    wrapped = finalize_b8_alert_surface(
        attach_derivatives_envelope(body, spine=spine, params=p),
        payload=p,
        spine=spine,
        display_timezone=p.get("display_timezone"),
    )
    disclosure = build_smart_alerts_disclosure(filtered)
    from launch57.identity_auth_common import attach_identity_auth_envelope

    adapted = _attach_habits_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=33,
        surface="smart_alerts",
        semantics=filtered,
        disclosure_key="smart_alerts_disclosure",
        disclosure=disclosure,
    )
    from launch57.billing_entitlement_common import attach_billing_entitlement_envelope

    adapted = attach_identity_auth_envelope(
        adapted,
        launch_item_id=33,
        surface_type="private",
        params=p,
    )
    return attach_billing_entitlement_envelope(adapted, launch_item_id=33, params=p)


_DISPATCH: dict[int, str] = {
    50: "order_book_intelligence",
    508: "l1_order_book_layer",
    56: "general_market_token_screener",
    19: "limited_watchlists",
    17: "smart_alerts_composite",
}


async def execute_launch57_derivatives_batch2(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_DERIVATIVES_BATCH2_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 derivatives batch 2")
    fn = globals()[_DISPATCH[capability_id]]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
