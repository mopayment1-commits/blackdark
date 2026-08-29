"""Tests — Data Sources & Intelligence (#140–#152)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_sources_layer as ds


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    ds.reset_data_sources_state()
    yield
    ds.reset_data_sources_state()


def test_140_white_label_deferred(seed):
    wl = ds.white_label_status_140(seed=seed)
    assert wl["duplicate_of"] == 90
    assert wl["powered_by_blackdark_required"] is True


def test_141_coindesk_dedup(seed):
    feed = ds.ingest_coindesk_feed_141(seed=seed)
    assert feed["deduplicated_count"] >= 1
    assert feed["items"][0]["attribution"] == "Source: CoinDesk"


def test_142_santiment_free_tier(seed):
    metrics = ds.ingest_santiment_metrics_142(seed=seed)
    assert metrics["free_tier_only"] is True
    assert "network_growth" in metrics["metrics"]


def test_143_event_calendar(seed):
    cal = ds.ingest_event_calendar_143(seed=seed)
    assert cal["context_only_not_recommendation"] is True
    assert len(cal["events"]) >= 1


def test_144_whale_alert(seed):
    whale = ds.ingest_whale_alert_144(seed=seed)
    assert whale["privacy_first"] is True
    assert whale["alerts"][0]["tx_hash"].startswith("0x")


def test_145_146_oracle_consensus(seed):
    consensus = ds.validate_oracle_consensus_145_146(seed=seed)
    assert consensus["consensus_accepted"] is True
    cmc = ds.ingest_cmc_price_145(seed=seed)
    coinbase = ds.ingest_coinbase_price_146(seed=seed)
    assert cmc["role"] == "secondary_redundancy"
    assert coinbase["role"] == "secondary_redundancy_regulated"


def test_147_trading_engine_rejected(seed):
    status = ds.signal_engine_status_147(seed=seed)
    assert status["trading_engine_rejected"] is True
    assert status["no_buy_sell_hold"] is True


def test_148_blockchain_com(seed):
    chain = ds.ingest_blockchain_com_148(seed=seed)
    assert chain["cross_validation_primary_rpc"] is True


def test_149_defillama(seed):
    defi = ds.ingest_defillama_149(seed=seed)
    assert defi["tvl_usd"] > 0
    assert defi["attribution"] == "Data: DefiLlama"


def test_150_opportunity_score(seed):
    score = ds.compute_opportunity_score_150(seed=seed)
    assert 0 <= score["opportunity_score"] <= 100
    assert score["formula_visible"] is True
    assert len(score["dimensions"]) == 8


def test_151_explain_opportunity(seed):
    explain = ds.explain_opportunity_151(asset="ETH", seed=seed)
    assert explain["asset"] == "ETH"
    assert "cvd" in explain["breakdown"]
    assert explain["insight_not_recommendation"] is True


def test_152_alerts_rejected_execution(seed):
    alerts = ds.alerts_execution_status_152(seed=seed)
    assert alerts["auto_execution_rejected"] is True
    assert alerts["alerts_existing"] is True


def test_150_top3_embed(seed):
    from bd_platform.retail_intelligence_layer import build_daily_top3_62

    top3 = build_daily_top3_62(seed=seed)
    assert "composite_score" in top3
    assert top3["opportunities"][0]["opportunity_score_composite"] > 0


def test_data_sources_e2e(seed):
    assert ds.run_data_sources_e2e_140_152(seed=seed)["all_passed"] is True
