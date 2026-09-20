"""
Launch-57 Phase 4 — Smart Money Batch 1.

Build order: #20 CAP-0092 → #16 CAP-0015/0071 → #17 CAP-0072/0075 → #13 CAP-0005 → #14 CAP-0006
"""

from __future__ import annotations

from typing import Any

from launch57.smart_money_common import (
    attach_smart_money_envelope,
    load_decision_spine,
    stale_gate_body,
    stamp_decision_batch,
)
from launch57.trust_adaptive_common import (
    apply_internal_flow_whale_significance_filter,
    attach_adaptive_disclosure,
    build_accumulation_distribution_disclosure,
    build_attribution_cohort_disclosure,
    build_exchange_flow_disclosure,
    build_internal_flow_filter_disclosure,
    build_level1_decision_disclosure,
    build_smart_money_screener_disclosure,
    build_whale_ratio_internal_flow_disclosure,
)

LAUNCH57_SMART_MONEY_BATCH1_CAP_IDS: frozenset[int] = frozenset({92, 15, 71, 72, 75, 5, 6})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    92: 20,
    15: 16,
    71: 16,
    72: 17,
    75: 17,
    5: 13,
    6: 14,
}

_BINDING = "launch57_phase4_smart_money_batch1"
_MODULE = "launch57.smart_money_batch1"


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


async def address_labels_cohorts(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #20 / CAP-0092 — limited address labels & cohorts nucleus."""
    from bd_platform.onchain_platform_layer import b2b_relationships_status_137

    p = dict(params or {})
    address = str(p.get("address") or "0x0000000000000000000000000000000000000000")
    blocked, spine = await _gated(
        capability_id=92,
        launch_item_id=20,
        surface="address_labels_cohorts",
        entrypoint="address_labels_cohorts",
        symbol=symbol,
        params={**p, "address": address},
    )
    if blocked:
        return blocked

    raw = b2b_relationships_status_137(seed=int(p.get("seed") or 0))
    labels = raw.get("labels") or raw.get("relationships") or []
    cohorts = {
        "limited_nucleus": True,
        "label_count": len(labels) if isinstance(labels, list) else 0,
        "labels": (labels[:25] if isinstance(labels, list) else labels),
        "scope": "launch57_limited_cohort_nucleus",
    }
    body = stamp_decision_batch(
        {
            "surface": "address_labels_cohorts",
            "symbol": spine["symbol"],
            "address": address,
            "success": bool(labels),
            "address_labels": labels,
            "cohorts": cohorts,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=92,
        launch_item_id=20,
        entrypoint="address_labels_cohorts",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_attribution_cohort_disclosure(labels=labels, cohorts=cohorts, payload=p)
    answer_state = "LABELED" if labels else "UNLABELED"
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=20,
        surface="address_labels_cohorts",
        answer_state=answer_state,
        disclosure_key="attribution_cohort_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if disclosure["coverage_qualified"] else "standard",
    )


async def exchange_flow_intelligence(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #16 / CAP-0015 — exchange flow in/out/net."""
    from cap646.dedicated_common import exchange_netflow_probe

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=15,
        launch_item_id=16,
        surface="exchange_flow_intelligence",
        entrypoint="exchange_flow_intelligence",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    exchange, netflow = exchange_netflow_probe(p, spine["symbol"])
    inflow = float(netflow.get("inflow_usd") or netflow.get("inflow") or 0)
    outflow = float(netflow.get("outflow_usd") or netflow.get("outflow") or 0)
    net = float(netflow.get("netflow_usd") or netflow.get("net") or (inflow - outflow))
    body = stamp_decision_batch(
        {
            "surface": "exchange_flow_intelligence",
            "symbol": spine["symbol"],
            "success": True,
            "exchange": exchange,
            "exchange_flow": {
                "inflow_usd": inflow,
                "outflow_usd": outflow,
                "netflow_usd": net,
                "raw": netflow,
                "price_context_from": "launch57.data_batch1",
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=15,
        launch_item_id=16,
        entrypoint="exchange_flow_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_exchange_flow_disclosure(
        exchange_flow=body["exchange_flow"],
        exchange=exchange,
        payload=p,
    )
    answer_state = "NET_INFLOW" if net > 0 else ("NET_OUTFLOW" if net < 0 else "NEUTRAL")
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=16,
        surface="exchange_flow_intelligence",
        answer_state=answer_state,
        disclosure_key="exchange_flow_disclosure",
        disclosure=disclosure,
    )


async def exchange_flow_netflow_layer(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #16 / CAP-0071 — netflow intelligence layer."""
    from bd_platform.heroes_capability_layer import exchange_netflow_intelligence_48

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=71,
        launch_item_id=16,
        surface="exchange_netflow",
        entrypoint="exchange_flow_netflow_layer",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    exchange = str(p.get("exchange") or "binance")
    netflow = exchange_netflow_intelligence_48(exchange=exchange, asset=spine["symbol"])
    body = stamp_decision_batch(
        {
            "surface": "exchange_netflow",
            "symbol": spine["symbol"],
            "success": True,
            "exchange": exchange,
            "netflow": netflow,
            "alias_launch_item": 16,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=71,
        launch_item_id=16,
        entrypoint="exchange_flow_netflow_layer",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_exchange_flow_disclosure(netflow=netflow, exchange=exchange, payload=p)
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=16,
        surface="exchange_netflow",
        answer_state="EXCHANGE_NETFLOW",
        disclosure_key="exchange_flow_disclosure",
        disclosure=disclosure,
    )


async def exchange_whale_ratio(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #17 / CAP-0072 — exchange whale ratio."""
    from bd_platform.market_analysis_layer import compute_whale_ls_ratio_114
    from exchange_internal_flow_filter import classify_flow

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=72,
        launch_item_id=17,
        surface="exchange_whale_ratio",
        entrypoint="exchange_whale_ratio",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    classified = classify_flow(
        from_address=str(p.get("from_address") or "0xexchange_hot"),
        to_address=str(p.get("to_address") or p.get("address") or "0x0000000000000000000000000000000000000000"),
        exchange=str(p.get("exchange") or "binance"),
        amount_usd=float(p.get("amount_usd") or 1_000_000),
        is_deposit=bool(p.get("is_deposit")),
        is_withdrawal=bool(p.get("is_withdrawal")),
    )
    payload = compute_whale_ls_ratio_114(seed=int(p.get("seed") or 0))
    significance = apply_internal_flow_whale_significance_filter(payload, classified)
    body = stamp_decision_batch(
        {
            "surface": "exchange_whale_ratio",
            "symbol": spine["symbol"],
            "success": significance.get("significance_eligible", False) or significance.get("exchange_whale_ratio") is not None,
            "exchange_whale_ratio": significance.get("exchange_whale_ratio"),
            "whale_ls_ratio": payload,
            "internal_flow_filter": classified,
            "whale_significance": significance,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=72,
        launch_item_id=17,
        entrypoint="exchange_whale_ratio",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_whale_ratio_internal_flow_disclosure(
        whale_payload=payload,
        internal_flow=classified,
        filtered=significance,
        payload=p,
    )
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=17,
        surface="exchange_whale_ratio",
        answer_state=str(significance.get("whale_bias") or "neutral"),
        disclosure_key="whale_ratio_internal_flow_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if significance.get("whale_significance_suppressed") else "standard",
    )


async def internal_flow_filter(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #17 / CAP-0075 — internal-flow filter."""
    from exchange_internal_flow_filter import classify_flow

    p = dict(params or {})
    address = str(p.get("address") or "0x0000000000000000000000000000000000000000")
    blocked, spine = await _gated(
        capability_id=75,
        launch_item_id=17,
        surface="internal_flow_filter",
        entrypoint="internal_flow_filter",
        symbol=symbol,
        params={**p, "address": address},
    )
    if blocked:
        return blocked

    classified = classify_flow(
        from_address=str(p.get("from_address") or "0xexchange_hot"),
        to_address=str(p.get("to_address") or address),
        exchange=str(p.get("exchange") or "binance"),
        amount_usd=float(p.get("amount_usd") or 1_000_000),
        is_deposit=bool(p.get("is_deposit")),
        is_withdrawal=bool(p.get("is_withdrawal")),
    )
    body = stamp_decision_batch(
        {
            "surface": "internal_flow_filter",
            "symbol": spine["symbol"],
            "success": True,
            "internal_flow_filter": classified,
            "alias_launch_item": 17,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=75,
        launch_item_id=17,
        entrypoint="internal_flow_filter",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_internal_flow_filter_disclosure(classified, payload=p)
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=17,
        surface="internal_flow_filter",
        answer_state=str(classified.get("classification") or "UNKNOWN"),
        disclosure_key="internal_flow_filter_disclosure",
        disclosure=disclosure,
    )


async def accumulation_distribution_detection(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #13 / CAP-0005 — accumulation / distribution detection."""
    from whale_signal_classifier import enrich_whale_narratives

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=5,
        launch_item_id=13,
        surface="smart_money_accumulation_detection",
        entrypoint="accumulation_distribution_detection",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    narratives = await enrich_whale_narratives(limit=int(p.get("limit") or 10))
    rows = narratives.get("narratives") or narratives.get("signals") or []
    filtered = [r for r in rows if spine["symbol"].upper() in str(r).upper()] or rows
    body = stamp_decision_batch(
        {
            "surface": "smart_money_accumulation_detection",
            "symbol": spine["symbol"],
            "success": bool(narratives),
            "accumulation_distribution": narratives,
            "signal_count": len(filtered) if isinstance(filtered, list) else 1,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=5,
        launch_item_id=13,
        entrypoint="accumulation_distribution_detection",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_accumulation_distribution_disclosure(
        narratives=narratives,
        signal_count=body["signal_count"],
        payload=p,
    )
    answer_state = "INFERRED" if body["signal_count"] else "UNCERTAIN"
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=13,
        surface="smart_money_accumulation_detection",
        answer_state=answer_state,
        disclosure_key="accumulation_distribution_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if disclosure["uncertainty_qualified"] else "standard",
    )


async def smart_money_token_screener(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #14 / CAP-0006 — smart money token screener."""
    from bd_platform.free_tier_capabilities import smart_money_leaderboard

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=6,
        launch_item_id=14,
        surface="smart_money_token_screener",
        entrypoint="smart_money_token_screener",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    board = await smart_money_leaderboard(limit=int(p.get("limit") or 25))
    tokens: dict[str, dict[str, Any]] = {}
    for row in board.get("leaderboard") or []:
        tok = str(row.get("symbol") or row.get("asset") or "").upper()
        if not tok:
            continue
        tokens.setdefault(tok, {"symbol": tok, "whale_events": 0, "total_usd": 0.0, "entities": []})
        tokens[tok]["whale_events"] += 1
        tokens[tok]["total_usd"] += float(row.get("amount_usd") or 0)
        tokens[tok]["entities"].append(row.get("entity"))

    screener = sorted(tokens.values(), key=lambda r: r["total_usd"], reverse=True)
    if spine["symbol"] != "BTC":
        screener = [r for r in screener if r["symbol"] == spine["symbol"]] or screener[:10]

    body = stamp_decision_batch(
        {
            "surface": "smart_money_token_screener",
            "symbol": spine["symbol"],
            "success": bool(screener),
            "screener": screener[:25],
            "count": len(screener),
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=6,
        launch_item_id=14,
        entrypoint="smart_money_token_screener",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_smart_money_screener_disclosure(screener=screener[:25], spine=spine, payload=p)
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=14,
        surface="smart_money_token_screener",
        answer_state="SCREENED",
        disclosure_key="smart_money_screener_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if not screener else "standard",
    )


_DISPATCH: dict[int, str] = {
    92: "address_labels_cohorts",
    15: "exchange_flow_intelligence",
    71: "exchange_flow_netflow_layer",
    72: "exchange_whale_ratio",
    75: "internal_flow_filter",
    5: "accumulation_distribution_detection",
    6: "smart_money_token_screener",
}


async def execute_launch57_smart_money_batch1(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_SMART_MONEY_BATCH1_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 smart money batch 1")
    fn = globals()[_DISPATCH[capability_id]]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
