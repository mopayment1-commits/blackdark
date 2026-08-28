"""Tests — Batch 29: #939 Events, #940 Entity Graph, #941 News, #942 DEX, #943/#944 Provenance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_entity_graph as graph
from bd_platform import data_engine_provenance_layer as provenance
from bd_platform import market_radar_crypto_events as events
from bd_platform import market_radar_curated_news as news
from bd_platform import onchain_intelligence_extension as onchain


@pytest.fixture
def events_seed() -> dict:
    return json.loads(Path("data/market_radar_crypto_events_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def graph_seed() -> dict:
    return json.loads(Path("data/data_engine_entity_graph_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def news_seed() -> dict:
    return json.loads(Path("data/market_radar_curated_news_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def onchain_seed() -> dict:
    return json.loads(Path("data/onchain_intelligence_extension_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def provenance_seed() -> dict:
    return json.loads(Path("data/data_engine_provenance_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    events.reset_crypto_events_state()
    graph.reset_entity_graph_state()
    yield
    events.reset_crypto_events_state()
    graph.reset_entity_graph_state()


# --- #939 Crypto Calendar / Events ---


def test_939_events_status(events_seed):
    status = events.crypto_events_status_939(seed=events_seed)
    assert status["standalone_rejected"] is True
    assert status["primary_source_links_required"] is True


def test_939_dedupe_and_classify(events_seed):
    cal = events.build_crypto_calendar_939(seed=events_seed)
    listing = [e for e in cal["events"] if e["event_type"] == "listing"]
    assert len(listing) >= 1
    assert listing[0]["source_count"] >= 2


def test_939_primary_source_links(events_seed):
    cal = events.build_crypto_calendar_939(seed=events_seed)
    for evt in cal["events"]:
        assert evt.get("primary_source_links")


def test_939_revisions(events_seed):
    rev = events.revise_event_date_939("evt_test", new_date="2026-10-01", seed=events_seed)
    assert rev["revision_logged"] is True


def test_939_unlock_alerts(events_seed):
    alerts = events.get_unlock_alerts_939(seed=events_seed)
    assert alerts["rule_based_only"] is True


def test_939_e2e(events_seed):
    e2e = events.run_crypto_events_e2e_939(seed=events_seed)
    assert e2e["all_passed"] is True


# --- #940 Entity Graph ---


def test_940_graph_status(graph_seed):
    status = graph.entity_graph_status_940(seed=graph_seed)
    assert status["standalone_rejected"] is True
    assert len(status["entity_types"]) == 7


def test_940_stable_ids(graph_seed):
    entity = graph.get_entity_940("ent_asset_btc", seed=graph_seed)
    assert entity["stable_id"] == "ent_asset_btc"


def test_940_provenance_edges(graph_seed):
    edges = graph.get_entity_edges_940("ent_protocol_uniswap", seed=graph_seed)
    assert edges["provenance_per_edge"] is True
    assert edges["temporal"] is True


def test_940_id_redirect(graph_seed):
    entity = graph.get_entity_940("ent_investor_andreessen", seed=graph_seed)
    assert entity["id_redirected"] is True


def test_940_merge_audit(graph_seed):
    audit = graph.get_merge_audit_940(seed=graph_seed)
    assert audit["count"] >= 1


def test_940_e2e(graph_seed):
    e2e = graph.run_entity_graph_e2e_940(seed=graph_seed)
    assert e2e["all_passed"] is True


# --- #941 Curated News ---


def test_941_news_status(news_seed):
    status = news.curated_news_status_941(seed=news_seed)
    assert status["standalone_rejected"] is True
    assert status["source_list_auditable"] is True


def test_941_dedupe(news_seed):
    feed = news.build_news_feed_941(seed=news_seed)
    btc_stories = [e for e in feed["feed"] if "BTC" in e.get("asset_tags", [])]
    assert any(e.get("source_count", 0) >= 2 for e in btc_stories)


def test_941_timestamps_preserved(news_seed):
    feed = news.build_news_feed_941(seed=news_seed)
    assert feed["timestamps_preserved"] is True


def test_941_trusted_sources(news_seed):
    sources = news.get_trusted_sources_941(seed=news_seed)
    assert sources["auditable"] is True
    assert sources["count"] >= 3


def test_941_e2e(news_seed):
    e2e = news.run_curated_news_e2e_941(seed=news_seed)
    assert e2e["all_passed"] is True


# --- #942 DEX Trading ---


def test_942_dex_status(onchain_seed):
    status = onchain.dex_trading_status_942(seed=onchain_seed)
    assert status["pool_mapping_audited"] is True
    assert status["wash_trading_policy"] == "flag_not_remove"


def test_942_dex_aggregation(onchain_seed):
    dash = onchain.build_dex_activity_dashboard_942(seed=onchain_seed)
    assert dash["ok"] is True
    assert dash["venue_count"] >= 1
    assert dash["rule_based_classification"] is True


def test_942_price_alignment(onchain_seed):
    dash = onchain.build_dex_activity_dashboard_942(seed=onchain_seed)
    assert len(dash.get("price_alignment_flags") or []) >= 1


def test_942_wash_flagged(onchain_seed):
    dash = onchain.build_dex_activity_dashboard_942(dex="uniswap", seed=onchain_seed)
    uni = next(v for v in dash["venues"] if v["dex"] == "uniswap")
    assert uni["wash_flagged_count"] >= 1


# --- #943 / #944 Provenance Layer ---


def test_943_audit_view(provenance_seed):
    audit = provenance.build_audit_view_943("aave_tvl", seed=provenance_seed)
    assert audit["end_to_end_traceable"] is True
    assert audit["audit_view_ops_only"] is True


def test_944_normalization(provenance_seed):
    norm = provenance.normalize_dataset_944("defi_protocol_metrics", seed=provenance_seed)
    assert norm["normalization_applied"] is True
    assert norm["audit_trail"] is not None


def test_945_e2e_includes_943_944(provenance_seed):
    e2e = provenance.run_provenance_layer_e2e(seed=provenance_seed)
    assert e2e["all_passed"] is True
    assert 943 in e2e["feature_refs"]
    assert 944 in e2e["feature_refs"]


# --- On-Chain Extension regression ---


def test_onchain_extension_e2e_batch29(onchain_seed):
    e2e = onchain.run_onchain_extension_e2e(seed=onchain_seed)
    assert e2e["all_passed"] is True
    assert 942 in e2e["feature_refs"]
