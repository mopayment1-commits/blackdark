"""Independent underlying tests for batch-04 hero wrappers and cross-ID bindings."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SEED = json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_330_simulate_spot_trade_underlying():
    from trade_simulator import simulate_spot_trade

    out = await simulate_spot_trade(symbol="BTC", side="buy", amount_usd=100.0)
    assert out.get("mode") == "spot_simulation"
    assert out.get("symbol") == "BTC"


def test_339_apply_opportunity_filter_underlying():
    from bd_platform.pro_trader_layer import apply_opportunity_filter_70

    out = apply_opportunity_filter_70(seed=SEED)
    assert out["ok"] is True


def test_356_ingest_cointelegraph_rss_underlying():
    from bd_platform.security_trust_data_layer import ingest_cointelegraph_rss_244

    out = ingest_cointelegraph_rss_244(seed=SEED)
    assert out["ok"] is True


def test_382_heroes_quality_manifest_underlying():
    from heroes_quality import heroes_quality_manifest

    manifest = heroes_quality_manifest()
    assert isinstance(manifest.get("heroes"), list)


def test_331_etf_reference_rates_inav_underlying():
    from bd_platform.charting_market_intelligence_layer import etf_reference_rates_inav_331

    out = etf_reference_rates_inav_331(seed=SEED)
    assert out["ok"] is True
    assert "inav_usd" in out


def test_363_tokenized_asset_coverage_underlying():
    from bd_platform.charting_market_intelligence_layer import tokenized_asset_coverage_363

    out = tokenized_asset_coverage_363(seed=SEED)
    assert out["ok"] is True


def test_379_analyze_liquidity_capacity_underlying():
    from bd_platform.arbitrage_portfolio_ux_layer import analyze_liquidity_capacity_189

    out = analyze_liquidity_capacity_189(asset="BTC", seed=SEED)
    assert out["ok"] is True


def test_390_build_exchange_health_underlying():
    from bd_platform.whales_institutional_layer import build_exchange_health_80

    out = build_exchange_health_80(exchange="binance", seed=SEED)
    assert out["ok"] is True


@pytest.mark.asyncio
async def test_316_sse_digest_status_underlying():
    from bd_platform.sse_stream import sse_digest_status_316

    out = await sse_digest_status_316(limit=3)
    assert out["ok"] is True
