"""Hero-to-catalog bridge for Batch05 capabilities #201–#250 (excluding REUSED-LINK #214/#245).

Strangler Fig pattern: hero semantics preserved; catalog surface is authoritative.
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any

def _catalog_goal(capability_id: int) -> str:
    from cap646.batch05_dedicated import EXPECTED_SURFACE

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


def _call(
    module_path: str,
    func_name: str,
    symbol: str,
    params: dict[str, Any],
    seed: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    mod = importlib.import_module(module_path)
    fn = getattr(mod, func_name)
    sig = inspect.signature(fn)
    param_names = set(sig.parameters)
    call_kwargs: dict[str, Any] = {"seed": seed, **kwargs}
    if "asset" in param_names and "asset" not in call_kwargs:
        call_kwargs["asset"] = symbol
    if "symbol" in param_names and "symbol" not in call_kwargs:
        call_kwargs["symbol"] = symbol
    if "address" in param_names and "address" not in call_kwargs:
        call_kwargs["address"] = str(params.get("address") or "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
    result = fn(**{k: v for k, v in call_kwargs.items() if k in param_names})
    if inspect.isawaitable(result):
        raise TypeError(f"{module_path}.{func_name} must be sync for batch05 hero bridge")
    return result


def _binding(module: str, func: str, **extra: Any) -> tuple[str, str, dict[str, Any]]:
    return (module, func, extra)


_HERO_BINDINGS: dict[int, tuple[str, str, dict[str, Any]]] = {
    201: _binding("bd_platform.derivatives_ta_research_layer", "quantitative_analysis_framework_201"),
    202: _binding("bd_platform.derivatives_ta_research_layer", "discover_hidden_opportunities_202"),
    203: _binding("bd_platform.derivatives_ta_research_layer", "run_derivatives_ta_research_e2e_192_203"),
    204: _binding("bd_platform.onchain_defi_sources_layer", "ingest_bscscan_204"),
    205: _binding("bd_platform.onchain_defi_sources_layer", "ingest_glassnode_metrics_205"),
    207: _binding("bd_platform.onchain_defi_sources_layer", "ingest_aave_data_207"),
    208: _binding("bd_platform.onchain_defi_sources_layer", "ingest_reddit_sentiment_208"),
    209: _binding("bd_platform.onchain_defi_sources_layer", "blockchain_wallets_status_209"),
    210: _binding("bd_platform.onchain_defi_sources_layer", "analyze_predictive_arbitrage_210"),
    211: _binding("bd_platform.onchain_defi_sources_layer", "cross_margin_risk_alert_211"),
    213: _binding("bd_platform.onchain_defi_sources_layer", "capital_allocation_insight_213"),
    215: _binding("bd_platform.onchain_defi_sources_layer", "flash_loan_gas_rejected_status_215"),
    216: _binding("bd_platform.onchain_defi_sources_layer", "run_onchain_defi_sources_e2e_204_216"),
    217: _binding("bd_platform.intelligence_market_extensions_layer", "analyze_best_venue_217"),
    218: _binding("bd_platform.intelligence_market_extensions_layer", "attach_order_journal_218", journal={"asset": "BTC"}),
    219: _binding("bd_platform.intelligence_market_extensions_layer", "analyze_nlp_sentiment_219"),
    220: _binding("bd_platform.intelligence_market_extensions_layer", "attach_pattern_outcome_220", backtest={"asset": "BTC"}),
    221: _binding("bd_platform.intelligence_market_extensions_layer", "market_slippage_analysis_221"),
    222: _binding("bd_platform.intelligence_market_extensions_layer", "monitor_exchange_latency_222"),
    223: _binding("bd_platform.intelligence_market_extensions_layer", "analyze_defi_fundamentals_223"),
    224: _binding("bd_platform.security_trust_data_layer", "coinmarketcal_status_245"),
    225: _binding("bd_platform.intelligence_market_extensions_layer", "pwa_strategy_status_225"),
    227: _binding("bd_platform.intelligence_market_extensions_layer", "run_intelligence_market_extensions_e2e_217_227"),
    229: _binding("bd_platform.intelligence_ux_extensions_layer", "attach_reasoning_explanation_229", explain={"asset": "BTC"}),
    230: _binding("bd_platform.intelligence_ux_extensions_layer", "analyze_cross_exchange_divergence_230"),
    231: _binding("bd_platform.intelligence_ux_extensions_layer", "triangular_arbitrage_status_231"),
    233: _binding("bd_platform.intelligence_ux_extensions_layer", "build_heatmap_component_233"),
    234: _binding("bd_platform.intelligence_ux_extensions_layer", "live_dashboard_status_234"),
    235: _binding("bd_platform.intelligence_ux_extensions_layer", "whale_intelligence_status_235"),
    236: _binding("bd_platform.intelligence_ux_extensions_layer", "subscription_tiers_status_236"),
    237: _binding("bd_platform.intelligence_ux_extensions_layer", "generate_market_summary_237"),
    238: _binding("bd_platform.intelligence_ux_extensions_layer", "scan_market_opportunities_238"),
    239: _binding("bd_platform.intelligence_ux_extensions_layer", "live_ta_status_239"),
    240: _binding("bd_platform.intelligence_ux_extensions_layer", "compute_s2f_240"),
    241: _binding("bd_platform.intelligence_ux_extensions_layer", "run_intelligence_ux_extensions_e2e_228_241"),
    242: _binding("bd_platform.security_trust_data_layer", "attach_audit_log_id_242", insight={"feature_ref": 242}),
    243: _binding("bd_platform.security_trust_data_layer", "ingest_bybit_price_243"),
    244: _binding("bd_platform.security_trust_data_layer", "ingest_cointelegraph_rss_244"),
    246: _binding("bd_platform.security_trust_data_layer", "list_etherscan_watchlist_246"),
    247: _binding("bd_platform.security_trust_data_layer", "generate_weekly_digest_247"),
    248: _binding("bd_platform.security_trust_data_layer", "manual_performance_tracker_248"),
    249: _binding("bd_platform.security_trust_data_layer", "trad_simulator_rejected_status_249"),
    250: _binding("bd_platform.security_trust_data_layer", "execution_speed_rejected_status_250"),
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
    module_path, func_name, extra_kwargs = _HERO_BINDINGS[capability_id]
    raw = _call(module_path, func_name, symbol, params, seed, **extra_kwargs)
    return _merge_raw(capability_id, symbol, raw)


def hero_binding_ids() -> frozenset[int]:
    return frozenset(_HERO_BINDINGS.keys())
