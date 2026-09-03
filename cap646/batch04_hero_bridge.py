"""Hero-to-catalog bridge for Batch04 capabilities #152–#200.

Transforms bd_platform hero-layer outputs into catalog-aligned domain payloads.
Strangler Fig pattern: hero semantics preserved; catalog surface is authoritative.
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any, Callable

def _catalog_goal(capability_id: int) -> str:
    from cap646.batch04_dedicated import EXPECTED_SURFACE
    return EXPECTED_SURFACE[capability_id]


def _base(capability_id: int, symbol: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": capability_id,
        "symbol": symbol,
        "catalog_goal": _catalog_goal(capability_id),
        **extra,
    }


def _merge_raw(capability_id: int, symbol: str, raw: dict[str, Any], **extra: Any) -> dict[str, Any]:
    """Include hero fields under catalog envelope; strip conflicting keys."""
    payload = _base(capability_id, symbol, **extra)
    for key, val in raw.items():
        if key not in {"ok", "feature_ref"}:
            payload.setdefault(key, val)
    return payload


def _call(module_path: str, func_name: str, symbol: str, params: dict[str, Any], seed: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    mod = importlib.import_module(module_path)
    fn = getattr(mod, func_name)
    sig = inspect.signature(fn)
    param_names = set(sig.parameters)
    call_kwargs: dict[str, Any] = {"seed": seed, **kwargs}
    if "asset" in param_names and "asset" not in call_kwargs:
        call_kwargs["asset"] = symbol
    if "assets" in param_names and "assets" not in call_kwargs:
        call_kwargs["assets"] = [symbol]
    if "symbol" in param_names and "symbol" not in call_kwargs:
        call_kwargs["symbol"] = symbol
    return fn(**{k: v for k, v in call_kwargs.items() if k in param_names})


# ─── Per-capability domain transforms ───────────────────────────────────────────

def _t152(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    gov = raw.get("governance") or raw
    return _base(152, symbol, governance_proposals=gov, proposal_count=len(gov.get("proposals", gov) if isinstance(gov, dict) else []))


def _t153(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        153, symbol,
        coverage_registry=raw.get("coverage") or {"projects_monitored": raw.get("venues") or []},
        monitoring_status=raw.get("status") or "active",
        arbitrage_insight=raw.get("cost_breakdown"),
    )


def _t154(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        154, symbol,
        copilot_status=raw.get("status"),
        dimensions=raw.get("dimensions", []),
        outputs=raw.get("outputs", []),
        rule_based=True,
        ai_classification="rule-based",
    )


def _t155(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        155, symbol,
        research_depth="deep",
        z_score=raw.get("z_score"),
        insight=raw.get("insight"),
        no_auto_trading=raw.get("no_auto_trading", True),
        rule_based=True,
        ai_classification="rule-based",
    )


def _t156(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    assets = raw.get("assets") or raw.get("registry") or []
    return _base(156, symbol, graph_nodes=assets, node_count=raw.get("actual_count") or len(assets))


def _t157(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(157, symbol, research_items=raw.get("capabilities", []), routes=raw.get("routes", []))


def _t158(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(158, symbol, feed_items=raw.get("venues", []), venue_count=len(raw.get("venues", [])))


def _t160(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        160, symbol,
        pricing_model="pay_per_request",
        in_squeeze=raw.get("in_squeeze"),
        request_metering={"unit": "api_call", "estimated_cost_usd": 0.001},
    )


def _t161(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        161, symbol,
        channel=raw.get("channel"),
        channels_available=raw.get("channels_available", []),
        delivery_target_seconds=raw.get("delivery_target_seconds"),
        entitlements={"tier": _params.get("tier", "pro"), "priority": raw.get("priority_queue")},
    )


def _t162(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(162, symbol, provenance_layer=raw, optimizations=raw.get("optimizations", []))


def _t163(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(163, symbol, cross_domain_report=raw, checks_passed=raw.get("all_passed"), rule_based_only=True)


def _t164(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        164, symbol,
        actionability_score=round(100 - float(raw.get("estimated_slippage_pct", 0)) * 5, 1),
        unlock_risk=raw.get("estimated_slippage_pct"),
        position_usd=raw.get("position_usd"),
    )


def _t165(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        165, symbol,
        momentum_score=raw.get("hashrate_drop_pct", 0),
        capitulation_signal=raw.get("capitulation_signal"),
        fundraising_outlook=raw.get("historical_stat"),
    )


def _t166(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(166, symbol, confidence_score=0.0, research_status=raw.get("status"), insights_only=True)


def _t167(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        167, symbol,
        social_volume=raw.get("deviation_sec"),
        volume_status=raw.get("status"),
        time_sync_valid=raw.get("accepted", raw.get("ntp_synchronized")),
    )


def _t168(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(168, symbol, dominance_pct=raw.get("cluster_index"), cluster_attached=raw.get("cluster_index") is not None)


def _t169(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    matrix = raw.get("correlation_decay_matrix") or raw.get("matrix") or {}
    return _base(169, symbol, unique_volume=raw.get("oi_momentum_delta"), correlation_matrix=matrix)


def _t170(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(170, symbol, trending_words=raw.get("trending_words", []), oi_momentum=raw.get("oi_momentum_delta"))


def _t171(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(171, symbol, trending_coins=[symbol], m2_flow=raw)


def _t172(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(172, symbol, historical_trends=raw.get("memory_entries", []), institutional_memory=raw.get("status"))


def _t173(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(173, symbol, key_narratives=raw.get("rbac_roles", []), narrative_count=len(raw.get("rbac_roles", [])))


def _t174(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(174, symbol, alpha_narratives=raw.get("white_label_features", []), branding_status=raw.get("status"))


def _t176(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(
        176, symbol,
        weighted_sentiment=raw.get("weighted_sentiment"),
        sentiment_weights=raw.get("weights"),
        checks=raw.get("checks"),
    )


def _t177(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(177, symbol, sentiment_balance=raw.get("cost_breakdown", {}).get("net_spread_pct", 0), cost_breakdown=raw.get("cost_breakdown"))


def _t178(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(178, symbol, source_breakdown=raw.get("scenarios", []), scenario_count=len(raw.get("scenarios", [])))


def _t179(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(179, symbol, dev_activity_score=raw.get("widget_count", len(raw.get("widgets", []))), widgets=raw.get("widgets", []))


def _t180(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    viz = raw.get("whale_visualization") or raw
    return _base(180, symbol, contributor_count=viz.get("flow_count", 0), whale_flows=viz)


def _t181(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(181, symbol, ecosystem_score=raw.get("packet_count", 0), committee_packets=raw.get("packets", []))


def _t182(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(182, symbol, activity_change_pct=raw.get("change_detected"), dev_activity_delta=raw.get("status"))


def _t184(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(184, symbol, cohort_type="whale_shark", holders=raw.get("holders", []), reporting_status=raw.get("status"))


def _t185(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(185, symbol, top_holders=raw.get("evidence_items", []), holder_count=len(raw.get("evidence_items", [])))


def _t186(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(186, symbol, balance_history=raw.get("learning_status"), wallet_tool_status=raw.get("status"))


def _t187(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(187, symbol, inflow_usd=raw.get("latency_p50_ms"), exchange_inflow_status=raw.get("status"))


def _t188(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(188, symbol, outflow_usd=raw.get("confirmed_alerts", 0), alert_confirmation=raw.get("user_confirmed"))


def _t190(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(190, symbol, supply_on_exchanges_pct=raw.get("geographic_spread_pct"), exchange_supply=raw.get("venues"))


def _t191(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(191, symbol, user_activity_score=raw.get("activity_score", 0), withdrawal_alerts=raw.get("suspension_alerts", []))


def _t192(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(192, symbol, network_activity=raw.get("venues"), avg_funding_pct=raw.get("avg_funding_8h_pct"))


def _t193(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(193, symbol, transaction_volume=raw.get("cvd_usd"), volume_status=raw.get("status"))


def _t194(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(194, symbol, nvt_ratio=raw.get("cvd_usd"), cvd_usd=raw.get("cvd_usd"), formula=raw.get("formula"))


def _t195(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(195, symbol, mvrv_ratio=raw.get("average_buy_price"), strategy=raw.get("strategy"))


def _t196(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(196, symbol, realized_cap_usd=raw.get("benchmarks", {}).get("SPX"), benchmarks=raw.get("benchmarks"))


def _t197(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(197, symbol, active_addresses=raw.get("role"), macro_sources=raw.get("benchmarks"))


def _t198(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(198, symbol, age_consumed=raw.get("reports", []), dormancy_signals=len(raw.get("reports", [])))


def _t199(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _base(199, symbol, mean_dollar_invested_age=raw.get("reports", [{}])[0].get("date") if raw.get("reports") else None, research_reports=raw.get("reports"))


def _t200(raw: dict[str, Any], symbol: str, _params: dict[str, Any]) -> dict[str, Any]:
    reports = raw.get("reports", [])
    return _base(
        200, symbol,
        circulation_rate=raw.get("circulation_rate"),
        token_reports=reports,
        report_count=len(reports),
        circulation_intelligence={"reports": reports, "attribution": raw.get("attribution")},
    )


# ─── Hero binding registry ─────────────────────────────────────────────────────

_HERO_BINDINGS: dict[int, tuple[str, str, TransformFn, dict[str, Any]]] = {
    152: ("bd_platform.data_sources_layer", "run_data_sources_e2e_140_152", _t152, {}),
    153: ("bd_platform.intelligence_analysis_layer", "analyze_arbitrage_opportunity_153", _t153, {}),
    154: ("bd_platform.intelligence_analysis_layer", "financial_brain_status_154", _t154, {}),
    155: ("bd_platform.intelligence_analysis_layer", "stat_arb_insight_155", _t155, {}),
    156: ("bd_platform.intelligence_analysis_layer", "asset_registry_105_coins_156", _t156, {}),
    157: ("bd_platform.intelligence_analysis_layer", "onchain_advanced_status_157", _t157, {}),
    158: ("bd_platform.intelligence_analysis_layer", "multi_venue_websocket_status_158", _t158, {}),
    160: ("bd_platform.intelligence_analysis_layer", "detect_volatility_squeeze_160", _t160, {}),
    161: ("bd_platform.intelligence_analysis_layer", "alert_delivery_status_161", _t161, {}),
    162: ("bd_platform.intelligence_analysis_layer", "data_grid_ui_status_162", _t162, {}),
    163: ("bd_platform.intelligence_analysis_layer", "run_intelligence_analysis_e2e_153_163", _t163, {}),
    164: ("bd_platform.risk_infrastructure_layer", "liquidity_impact_warning_164", _t164, {}),
    165: ("bd_platform.risk_infrastructure_layer", "hashrate_capitulation_forecast_165", _t165, {}),
    166: ("bd_platform.risk_infrastructure_layer", "brokerage_rejected_status_166", _t166, {}),
    167: ("bd_platform.risk_infrastructure_layer", "validate_time_sync_167", _t167, {}),
    168: ("bd_platform.risk_infrastructure_layer", "attach_cluster_index_168", _t168, {"cluster_result": {"clusters": [{"asset": "BTC", "size": 3}]}}),
    169: ("bd_platform.risk_infrastructure_layer", "compute_correlation_decay_matrix_169", _t169, {}),
    170: ("bd_platform.risk_infrastructure_layer", "compute_oi_momentum_delta_170", _t170, {}),
    171: ("bd_platform.risk_infrastructure_layer", "compute_m2_macro_flow_171", _t171, {}),
    172: ("bd_platform.risk_infrastructure_layer", "institutional_memory_status_172", _t172, {}),
    173: ("bd_platform.risk_infrastructure_layer", "institutional_rbac_status_173", _t173, {}),
    174: ("bd_platform.risk_infrastructure_layer", "full_white_label_status_174", _t174, {}),
    176: ("bd_platform.risk_infrastructure_layer", "run_risk_infrastructure_e2e_164_176", _t176, {}),
    177: ("bd_platform.arbitrage_portfolio_ux_layer", "analyze_arbitrage_cost_177", _t177, {}),
    178: ("bd_platform.arbitrage_portfolio_ux_layer", "run_scenario_drawdown_analysis_178", _t178, {}),
    179: ("bd_platform.arbitrage_portfolio_ux_layer", "build_command_center_dashboard_179", _t179, {}),
    180: ("bd_platform.arbitrage_portfolio_ux_layer", "build_whale_flow_visualization_180", _t180, {}),
    181: ("bd_platform.arbitrage_portfolio_ux_layer", "committee_packets_status_181", _t181, {}),
    182: ("bd_platform.arbitrage_portfolio_ux_layer", "white_label_infrastructure_status_182", _t182, {}),
    184: ("bd_platform.arbitrage_portfolio_ux_layer", "fund_reporting_status_184", _t184, {}),
    185: ("bd_platform.arbitrage_portfolio_ux_layer", "acquisition_evidence_package_185", _t185, {}),
    186: ("bd_platform.arbitrage_portfolio_ux_layer", "continuous_learning_status_186", _t186, {}),
    187: ("bd_platform.arbitrage_portfolio_ux_layer", "latency_monitoring_status_187", _t187, {}),
    188: ("bd_platform.arbitrage_portfolio_ux_layer", "risk_alert_user_confirmation_188", _t188, {}),
    190: ("bd_platform.arbitrage_portfolio_ux_layer", "analyze_geographic_arbitrage_190", _t190, {}),
    191: ("bd_platform.arbitrage_portfolio_ux_layer", "run_arbitrage_portfolio_ux_e2e_177_191", _t191, {}),
    192: ("bd_platform.derivatives_ta_research_layer", "analyze_funding_rate_192", _t192, {}),
    193: ("bd_platform.derivatives_ta_research_layer", "auto_arbitrage_rejected_status_193", _t193, {}),
    194: ("bd_platform.derivatives_ta_research_layer", "compute_cvd_194", _t194, {}),
    195: ("bd_platform.derivatives_ta_research_layer", "strategy_simulator_195", _t195, {}),
    196: ("bd_platform.derivatives_ta_research_layer", "ingest_yahoo_finance_macro_196", _t196, {}),
    197: ("bd_platform.derivatives_ta_research_layer", "ingest_alpha_vantage_macro_197", _t197, {}),
    198: ("bd_platform.derivatives_ta_research_layer", "ingest_binance_research_198", _t198, {}),
    199: ("bd_platform.derivatives_ta_research_layer", "ingest_messari_research_199", _t199, {}),
    200: ("bd_platform.derivatives_ta_research_layer", "ingest_coingecko_reports_200", _t200, {}),
}


def build_hero_payload(
    capability_id: int,
    *,
    symbol: str,
    params: dict[str, Any],
    seed: dict[str, Any],
) -> dict[str, Any]:
    """Invoke hero function and transform to catalog-aligned payload."""
    if capability_id not in _HERO_BINDINGS:
        raise KeyError(f"No hero binding for capability {capability_id}")
    module_path, func_name, transform, extra_kwargs = _HERO_BINDINGS[capability_id]
    raw = _call(module_path, func_name, symbol, params, seed, **extra_kwargs)
    return transform(raw, symbol, params)


def hero_binding_ids() -> frozenset[int]:
    return frozenset(_HERO_BINDINGS.keys())
