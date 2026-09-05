"""Tests for Batch05 Strangler spine — catalog-correct wiring."""

from __future__ import annotations

import inspect

import pytest

from cap646.batch05_dedicated import EXPECTED_SURFACE, execute
from cap646.batch05_strangler_spine import STRANGLER_BUILDERS, STRANGLER_IMPLEMENTED_IDS

WAVE1_IDS = [201, 202, 203, 204]
WAVE2A_IDS = [205]
WAVE2B_IDS = [207, 208, 209, 210, 211, 213, 215, 216]
WAVE3_IDS = [217, 218, 219, 220, 221, 222, 223, 224, 225, 227]
WAVE4_IDS = [229, 230, 231, 233, 234, 235, 236, 237, 238, 239, 240, 241]
WAVE5_IDS = [242, 243, 244, 246, 247, 248, 249, 250]
ALL_STRANGLER_IDS = sorted(STRANGLER_IMPLEMENTED_IDS)


@pytest.mark.parametrize("capability_id", ALL_STRANGLER_IDS)
def test_strangler_builder_registered(capability_id: int):
    assert capability_id in STRANGLER_BUILDERS
    assert STRANGLER_BUILDERS[capability_id].__name__.startswith("build_")


@pytest.mark.parametrize("capability_id", ALL_STRANGLER_IDS)
@pytest.mark.asyncio
async def test_strangler_builder_returns_catalog_payload(capability_id: int):
    builder = STRANGLER_BUILDERS[capability_id]
    sig = inspect.signature(builder)
    kwargs: dict = {"symbol": "BTC", "params": {"tier": "pro"}}
    if "seed" in sig.parameters:
        from cap646.dedicated_common import seed

        kwargs["seed"] = seed()
    payload = await builder(**kwargs)
    root = EXPECTED_SURFACE[capability_id]
    assert payload["ok"] is True
    assert payload["feature_ref"] == capability_id
    assert payload["catalog_goal"] == root
    assert payload.get("miswire_remediation") == "STRANGLER_IMPLEMENTED"
    assert payload["latency_ms"] >= 0
    assert payload["latency_ms"] < 5000


@pytest.mark.parametrize("capability_id", ALL_STRANGLER_IDS)
@pytest.mark.asyncio
async def test_strangler_runtime_dispatch(capability_id: int):
    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        },
    )
    root = EXPECTED_SURFACE[capability_id]
    assert result["success"] is True
    assert result["surface"] == root
    assert result[root]["feature_ref"] == capability_id
    assert result[root].get("miswire_remediation") == "STRANGLER_IMPLEMENTED"


@pytest.mark.asyncio
async def test_cap205_open_interest_binance_futures():
    result = await execute(205, params={"symbol": "BTC"})
    payload = result["open_interest_intelligence"]
    assert payload["source"] == "free_market_data.binance_futures_snapshot"
    assert "open_interest_usd" in payload


@pytest.mark.asyncio
async def test_cap232_reused_link_to_strangler_205():
    result = await execute(232, params={"symbol": "BTC"})
    assert result["classification"] == "REUSED-LINK"
    assert result["catalog_link"]["canonical_capability_id"] == 205
    assert result["catalog_link"]["binding"] == "cap646/batch05_strangler_spine.py::build_open_interest_205"
    assert result["open_interest_intelligence"]["miswire_remediation"] == "STRANGLER_IMPLEMENTED"


@pytest.mark.parametrize("capability_id,source", [
    (207, "market_context.probe_price_sources+free_market_data.binance_futures_snapshot"),
    (208, "free_market_data.binance_futures_snapshot"),
    (209, "cap646.fallbacks.resolve_ohlcv_closes"),
    (210, "bd_platform.market_rankings.market_rankings"),
    (211, "bd_platform.market_rankings.market_rankings"),
    (213, "footprint_analytics.footprint_snapshot"),
    (215, "onchain_defi_sources_layer.ingest_reddit_sentiment_208"),
    (216, "market_rankings+onchain_defi_sources_layer.ingest_reddit_sentiment_208"),
])
@pytest.mark.asyncio
async def test_wave2b_catalog_sources(capability_id: int, source: str):
    result = await execute(capability_id, params={"symbol": "BTC"})
    root = EXPECTED_SURFACE[capability_id]
    assert result[root]["source"] == source


@pytest.mark.parametrize("capability_id,source", [
    (217, "intelligence_market_extensions_layer.analyze_best_venue_217"),
    (218, "intelligence_market_extensions_layer.list_manual_order_journal_218"),
    (219, "intelligence_market_extensions_layer.analyze_nlp_sentiment_219"),
    (220, "intelligence_market_extensions_layer.analyze_pattern_outcome_220"),
    (221, "intelligence_market_extensions_layer.market_slippage_analysis_221"),
    (222, "intelligence_market_extensions_layer.monitor_exchange_latency_222"),
    (223, "intelligence_market_extensions_layer.analyze_defi_fundamentals_223"),
    (224, "intelligence_market_extensions_layer.analyze_token_dcf_224"),
    (225, "intelligence_market_extensions_layer.pwa_strategy_status_225"),
    (227, "intelligence_market_extensions_layer.analyze_etf_premium_227"),
])
@pytest.mark.asyncio
async def test_wave3_catalog_sources(capability_id: int, source: str):
    result = await execute(capability_id, params={"symbol": "BTC"})
    root = EXPECTED_SURFACE[capability_id]
    assert result[root]["source"] == source
    assert result[root]["miswire_remediation"] == "STRANGLER_IMPLEMENTED"


@pytest.mark.asyncio
async def test_wave3_cap218_record_order_path():
    result = await execute(
        218,
        params={"symbol": "BTC", "record_order": True, "target_price": 65000, "state": "Filled", "filled_price": 65100},
    )
    payload = result["google_sheets_integration"]
    assert payload["ok"] is True
    assert len(payload.get("journal_entries") or []) >= 1


@pytest.mark.asyncio
async def test_wave3_cap224_fixes_hero_miswire():
    """#224 hero bridge pointed at coinmarketcal_status_245 — strangler uses token DCF."""
    result = await execute(224, params={"symbol": "BTC", "protocol": "aave"})
    payload = result["narrative_actionability_score"]
    assert payload["source"] == "intelligence_market_extensions_layer.analyze_token_dcf_224"
    assert payload["token_dcf"]["no_fair_value_guarantee"] is True


@pytest.mark.parametrize("capability_id,source", [
    (229, "intelligence_ux_extensions_layer.generate_reasoning_explanation_229"),
    (230, "intelligence_ux_extensions_layer.analyze_cross_exchange_divergence_230"),
    (231, "intelligence_ux_extensions_layer.triangular_arbitrage_status_231"),
    (233, "intelligence_ux_extensions_layer.build_heatmap_component_233"),
    (234, "intelligence_ux_extensions_layer.live_dashboard_status_234"),
    (235, "intelligence_ux_extensions_layer.whale_intelligence_status_235"),
    (236, "intelligence_ux_extensions_layer.subscription_tiers_status_236"),
    (237, "intelligence_ux_extensions_layer.generate_market_summary_237"),
    (238, "intelligence_ux_extensions_layer.scan_market_opportunities_238"),
    (239, "intelligence_ux_extensions_layer.live_ta_status_239"),
    (240, "intelligence_ux_extensions_layer.compute_s2f_240"),
    (241, "intelligence_ux_extensions_layer.ingest_fred_macro_241"),
])
@pytest.mark.asyncio
async def test_wave4_catalog_sources(capability_id: int, source: str):
    result = await execute(capability_id, params={"symbol": "BTC"})
    root = EXPECTED_SURFACE[capability_id]
    assert result[root]["source"] == source
    assert result[root]["miswire_remediation"] == "STRANGLER_IMPLEMENTED"


@pytest.mark.asyncio
async def test_wave4_cap241_fixes_hero_miswire():
    """#241 hero bridge used e2e runner — strangler uses FRED macro ingest."""
    result = await execute(241, params={"symbol": "BTC"})
    payload = result["sentiment_intelligence"]
    assert payload["source"] == "intelligence_ux_extensions_layer.ingest_fred_macro_241"
    assert "FRED" in payload["fred_macro"]["attribution"]


@pytest.mark.parametrize("capability_id,source", [
    (242, "security_trust_data_layer.attach_audit_log_id_242"),
    (243, "security_trust_data_layer.ingest_bybit_price_243"),
    (244, "security_trust_data_layer.ingest_cointelegraph_rss_244"),
    (246, "security_trust_data_layer.list_etherscan_watchlist_246"),
    (247, "security_trust_data_layer.generate_weekly_digest_247"),
    (248, "security_trust_data_layer.manual_performance_tracker_248"),
    (249, "security_trust_data_layer.trad_simulator_rejected_status_249"),
    (250, "security_trust_data_layer.execution_speed_rejected_status_250"),
])
@pytest.mark.asyncio
async def test_wave5_catalog_sources(capability_id: int, source: str):
    result = await execute(capability_id, params={"symbol": "BTC"})
    root = EXPECTED_SURFACE[capability_id]
    assert result[root]["source"] == source
    assert result[root]["miswire_remediation"] == "STRANGLER_IMPLEMENTED"


@pytest.mark.asyncio
async def test_wave5_cap242_audit_log_attached():
    result = await execute(242, params={"symbol": "BTC"})
    payload = result["price_prediction_multi_signal_forecast"]
    assert payload["audit_log_id"]
    assert 242 in (payload.get("merged_features") or [])


@pytest.mark.asyncio
async def test_wave5_cap249_250_rejected_boundaries():
    r249 = await execute(249, params={"symbol": "BTC"})
    assert r249["cli_access"]["trad_simulator_rejected"] is True
    r250 = await execute(250, params={"symbol": "BTC"})
    assert r250["openapi_sdk_generation"]["execution_speed_rejected"] is True


def test_wave5_strangler_count_complete():
    assert len(STRANGLER_IMPLEMENTED_IDS) == 43
    assert set(WAVE5_IDS).issubset(STRANGLER_IMPLEMENTED_IDS)
    assert 245 not in STRANGLER_IMPLEMENTED_IDS
