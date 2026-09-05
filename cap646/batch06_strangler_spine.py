"""Batch06 Strangler spine — catalog-correct wiring for IDs 251–300.

REUSED-LINK IDs are handled in ``batch06_dedicated.py``.
Miswired hero/security_trust suffix bindings (e.g. compute_token_velocity_251) are NOT used.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import time
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.dedicated_common import holder_analytics_bundle, seed as _default_seed

CatalogGoal = str
Builder = Callable[..., Awaitable[dict[str, Any]]]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _base(capability_id: int, symbol: str, catalog_goal: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": capability_id,
        "symbol": symbol.upper(),
        "catalog_goal": catalog_goal,
        "rule_based": True,
        "ai_classification": "rule-based",
        "ai_drift_monitoring": "N/A",
        "data_freshness": _utcnow(),
        **extra,
    }


def _timed(extra: dict[str, Any], t0: float) -> dict[str, Any]:
    extra["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    extra.setdefault("performance_tier", "fast" if extra["latency_ms"] < 500 else "moderate")
    return extra


async def _call_binding(
    module_path: str,
    entrypoint: str,
    *,
    symbol: str,
    params: dict[str, Any],
    seed: dict[str, Any] | None = None,
) -> Any:
    mod = importlib.import_module(module_path)
    fn = getattr(mod, entrypoint)
    kwargs: dict[str, Any] = {}
    sig = inspect.signature(fn)
    if "symbol" in sig.parameters:
        kwargs["symbol"] = symbol
    elif "asset" in sig.parameters:
        kwargs["asset"] = symbol
    if "seed" in sig.parameters:
        kwargs["seed"] = seed or _default_seed()
    if "params" in sig.parameters:
        kwargs["params"] = params
    if "address" in sig.parameters and params.get("address"):
        kwargs["address"] = params["address"]
    if "text" in sig.parameters and params.get("text"):
        kwargs["text"] = params["text"]
    if "symbols" in sig.parameters:
        kwargs["symbols"] = params.get("symbols") or [symbol]
    if "limit" in sig.parameters and params.get("limit") is not None:
        kwargs["limit"] = params["limit"]
    if asyncio.iscoroutinefunction(fn):
        return await fn(**kwargs)
    return await asyncio.to_thread(fn, **kwargs)


def _make_builder(
    capability_id: int,
    catalog_goal: str,
    module_path: str,
    entrypoint: str,
    *,
    payload_key: str | None = None,
    attribution: str = "",
) -> Builder:
    async def _builder(*, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        raw = await _call_binding(module_path, entrypoint, symbol=symbol, params=params, seed=seed)
        key = payload_key or catalog_goal
        payload = _base(
            capability_id,
            symbol,
            catalog_goal,
            **{key: raw},
            source=f"{module_path}.{entrypoint}",
            attribution=attribution or f"Catalog-aligned binding for #{capability_id}",
            miswire_remediation="STRANGLER_IMPLEMENTED",
        )
        if isinstance(raw, dict):
            for k in ("timestamp", "data_source", "alerts", "metrics", "cells"):
                if k in raw and k not in payload:
                    payload[k] = raw[k]
        return _timed(payload, t0)

    _builder.__name__ = f"build_{catalog_goal}_{capability_id}"
    return _builder


async def build_liquidation_heatmap_252(*, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.liquidation_radar import liquidation_radar

    radar = await liquidation_radar(symbol)
    payload = _base(
        252,
        symbol,
        "liquidation_heatmap",
        liquidation_heatmap=radar,
        alerts=radar.get("alerts"),
        metrics=radar.get("metrics"),
        source="bd_platform.liquidation_radar.liquidation_radar",
        attribution="Liquidation heatmap via Binance + optional CoinGlass supplement",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_transaction_search_279(*, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    from onchain_tracker import build_onchain_context_safe

    ctx = await build_onchain_context_safe()
    payload = _base(
        279,
        symbol,
        "transaction_search",
        transaction_search=ctx,
        flow_assets=len(ctx.get("assets") or ctx.get("flows") or []),
        source="onchain_tracker.build_onchain_context_safe",
        attribution="On-chain flow context as transaction search proxy — insight only",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_token_top_holders_288(*, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    dist, metrics = await holder_analytics_bundle(symbol)
    payload = _base(
        288,
        symbol,
        "token_top_holders",
        token_top_holders=dist,
        holder_metrics=metrics,
        top_holders=(dist.get("top_holders") or dist.get("distribution") or [])[:10],
        source="cap646.dedicated_common.holder_analytics_bundle",
        attribution="Holder distribution as token top holders proxy",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_cross_entity_decision_299(*, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    from trust_pulse import build_trust_pulse

    pulse = await build_trust_pulse(symbol=symbol)
    payload = _base(
        299,
        symbol,
        "cross_entity_decision_intelligence",
        cross_entity_decision=pulse,
        trust_score=pulse.get("trust_score"),
        source="trust_pulse.build_trust_pulse",
        attribution="Cross-entity trust pulse — not execution advice",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_options_volume_263(*, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        from options_fetcher import fetch_options_overview

        overview = await fetch_options_overview(symbol)
        source = "options_fetcher.fetch_options_overview"
    except Exception:
        from bd_platform.derivatives_onchain_intelligence_layer import options_volume_263

        overview = options_volume_263(symbol=symbol, seed=seed or _default_seed())
        source = "bd_platform.derivatives_onchain_intelligence_layer.options_volume_263"
    payload = _base(
        263,
        symbol,
        "options_volume",
        options_volume=overview,
        source=source,
        attribution="Options volume by tenor",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_order_book_depth_267(*, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.footprint_analytics import footprint_snapshot

    book = await footprint_snapshot(symbol)
    payload = _base(
        267,
        symbol,
        "order_book_market_depth",
        order_book_market_depth=book,
        venue_count=len(book.get("top_of_book") or []),
        source="bd_platform.footprint_analytics.footprint_snapshot",
        attribution="Multi-venue order book depth proxy",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


# Derivatives/onchain layer sync bindings (262–300 except special-cased above)
_DERIV_LAYER_BINDINGS: dict[int, tuple[str, str]] = {
    262: ("options_open_interest_262", "options_open_interest"),
    264: ("options_iv_skew_264", "options_iv_skew"),
    265: ("max_pain_gamma_context_265", "max_pain_gamma_context"),
    266: ("spot_market_intelligence_266", "spot_market_intelligence"),
    268: ("historical_derivatives_data_268", "historical_derivatives_data"),
    269: ("exchange_comparison_269", "exchange_comparison"),
    270: ("liquidation_cascade_proximity_270", "liquidation_cascade_proximity"),
    271: ("leverage_pressure_score_271", "leverage_pressure_score"),
    273: ("multi_model_liquidation_comparison_273", "multi_model_liquidation_comparison"),
    274: ("derivatives_alerts_status_274", "derivatives_alerts"),
    276: ("entity_resolution_engine_276", "entity_resolution_engine"),
    277: ("address_labeling_system_277", "address_labeling_system"),
    278: ("entity_profiles_278", "entity_profiles"),
    280: ("portfolio_holdings_280", "portfolio_holdings"),
    281: ("balance_history_281", "balance_history"),
    282: ("entity_pnl_282", "entity_pnl"),
    283: ("exchange_usage_intelligence_283", "exchange_usage_intelligence"),
    284: ("top_counterparties_284", "top_counterparties"),
    285: ("network_graph_visualizer_285", "network_graph_visualizer"),
    286: ("automated_trace_path_finding_286", "automated_trace_path_finding"),
    287: ("cross_chain_trace_287", "cross_chain_trace"),
    289: ("token_exchange_flows_289", "token_exchange_flows"),
    290: ("token_transaction_explorer_290", "token_transaction_explorer"),
    293: ("private_labels_status_293", "private_labels"),
    294: ("portfolio_archive_snapshot_294", "portfolio_archive_snapshot"),
    295: ("ai_market_insights_295", "ai_market_insights"),
    296: ("whale_movement_intelligence_296", "whale_movement_intelligence"),
    297: ("fraud_suspicious_activity_297", "fraud_suspicious_activity"),
    298: ("api_onchain_intelligence_298", "api_onchain_intelligence"),
    300: ("advanced_multi_asset_charting_300", "advanced_multi_asset_charting"),
}

_MODULE_MAP_BINDINGS: dict[int, tuple[str, str, str]] = {
    253: ("bd_platform.liquidation_radar", "liquidation_radar", "liquidation_map_levels"),
    254: ("bd_platform.liquidation_radar", "liquidation_radar", "real_time_liquidation_events"),
    258: ("bd_platform.free_market_data", "binance_futures_snapshot", "top_trader_positioning"),
    275: ("trust_pulse", "build_trust_pulse", "cross_domain_decision_intelligence"),
}

for _cid, (_fn, _goal) in _DERIV_LAYER_BINDINGS.items():
    _MODULE_MAP_BINDINGS[_cid] = (
        "bd_platform.derivatives_onchain_intelligence_layer",
        _fn,
        _goal,
    )

STRANGLER_BUILDERS: dict[int, Builder] = {
    252: build_liquidation_heatmap_252,
    263: build_options_volume_263,
    267: build_order_book_depth_267,
    279: build_transaction_search_279,
    288: build_token_top_holders_288,
    299: build_cross_entity_decision_299,
}

for _cid, (mod, ep, goal) in _MODULE_MAP_BINDINGS.items():
    if _cid not in STRANGLER_BUILDERS and _cid not in {251, 255, 256, 257, 259, 260, 261, 272, 275, 291, 292}:
        STRANGLER_BUILDERS[_cid] = _make_builder(_cid, goal, mod, ep)

# 275 is REUSED-LINK in dedicated — remove from strangler if added
STRANGLER_BUILDERS.pop(275, None)
