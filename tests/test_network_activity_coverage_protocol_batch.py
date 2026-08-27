"""Tests — #682 Network Activity, #684 Coverage Registry, #685 Protocol Directory."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import asset_registry as ar
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import investment_thesis_scoring as its
from bd_platform import onchain_metrics_library as oml
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def registry_seed(tmp_path, monkeypatch):
    p = tmp_path / "asset_registry_seed.json"
    p.write_text(Path("data/asset_registry_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ar, "_SEED_PATH", p)
    return p


@pytest.fixture
def dos_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_opportunity_scanner_seed.json"
    p.write_text(Path("data/defi_opportunity_scanner_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dos, "_SEED_PATH", p)
    return p


# --- #682 Network Activity ---


def test_682_five_mandatory_metrics(oml_seed):
    suite = oml.build_network_activity_suite_682("BTC")
    assert suite["ok"] is True
    assert len(suite["mandatory_metrics"]) == 5
    assert suite["metrics"]["tx_count"]["value"] is not None
    assert suite["metrics"]["active_addresses_daa"]["value"] is not None


def test_682_chain_specific_definitions(oml_seed):
    btc = oml.build_network_activity_suite_682("BTC")
    eth = oml.build_network_activity_suite_682("ETH")
    hbar = oml.build_network_activity_suite_682("HBAR")
    assert btc["chain_model"] == "utxo"
    assert eth["chain_model"] == "account"
    assert hbar["chain_model"] == "dag"
    assert btc["chain_specific_definitions_documented"] is True


def test_682_reorg_handling(oml_seed):
    suite = oml.build_network_activity_suite_682("ETH")
    reorg = suite["reorg_handling"]
    assert reorg["enabled"] is True
    assert reorg["recalculate_cancelled_blocks"] is True
    assert reorg["metrics_recalculated"] is True


def test_682_qa_reconciliation(oml_seed):
    qa = oml.run_network_activity_qa_reconciliation_682("BTC")
    assert qa["within_tolerance"] is True
    assert qa["parity_delta_pct"] <= qa["parity_tolerance_pct"]


def test_682_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_network_activity_widget_682("ETH")
    assert widget["ok"] is True
    assert widget["widget_label_ar"] == "نشاط الشبكة"


def test_682_daily_brief_hook(oml_seed):
    brief = oml.build_network_activity_daily_brief_hook_474()
    assert brief is not None
    assert brief.get("integration_682") is True
    assert "DAA" in brief.get("mention_en", "")


def test_682_thesis_growth_dimension(oml_seed):
    dim = oml.score_network_growth_thesis_dimension_682("ETH")
    assert dim["ok"] is True
    thesis = its.score_investment_thesis("ETH")
    on_chain_growth = (thesis.get("dimensions") or {}).get("on_chain_growth")
    assert on_chain_growth is not None


def test_682_metrics_library_panel(oml_seed):
    panel = oml.build_metrics_library_panel("BTC")
    assert panel["sub_modules"]["682_network_activity"]["ok"] is True


# --- #684 Coverage Registry ---


def test_684_coverage_badges(registry_seed):
    panel = ar.build_asset_registry_panel(symbol="BTC")
    badges = panel["asset"]["coverage_badges_684"]
    assert badges["ok"] is True
    assert len(badges["badges"]) == 5
    assert "🟢" in badges["badge_display"]
    assert badges["flags_reflect_backend_availability"] is True


def test_684_unlocks_red_when_backend_down(registry_seed):
    panel = ar.build_asset_registry_panel(symbol="BTC")
    unlocks = panel["asset"]["coverage_badges_684"]["badges"]["unlocks"]
    assert unlocks["emoji"] == "🔴"
    assert unlocks["backend_available"] is False


def test_684_coverage_parity_tests(registry_seed):
    parity = ar.run_coverage_parity_tests_684()
    assert parity["all_passed"] is True


def test_684_opportunity_filter(registry_seed):
    opps = [{"opportunity_id": "defi_low_coverage_001", "asset": "GAL", "net_edge_usdt": 50}]
    kept, cancelled = ar.filter_opportunities_by_coverage_684(opps)
    assert len(cancelled) == 1
    assert cancelled[0]["cancelled_by_coverage_684"] is True


def test_684_uae_integration(registry_seed):
    feed = uae.build_unified_feed()
    assert "cancelled_by_coverage_684" in feed


# --- #685 Protocol Directory ---


def test_685_protocol_profile(registry_seed):
    profile = ar.build_protocol_profile("aave")
    assert profile["ok"] is True
    assert profile["mandatory_fields_met"] is True
    assert profile["category"] == "Lending"
    assert profile["route"] == "/protocol/aave"
    assert profile["stable_id"] == "proto_aave_v3"


def test_685_protocol_directory(registry_seed):
    directory = ar.build_protocol_directory_685()
    assert directory["ok"] is True
    assert directory["protocol_count"] >= 4
    assert "LST" in directory["categories"]


def test_685_defi_scanner_integration(dos_seed, registry_seed):
    panel = dos.build_defi_panel()
    proto = panel.get("protocol_directory_685") or {}
    assert proto.get("ok") is True
    assert proto.get("protocol_count", 0) >= 3


def test_682_reconciliation(oml_seed):
    qa = oml.run_historical_qa_tests()
    names = {t["test"] for t in qa["reconciliation_tests"]}
    assert "network_activity_suite_682" in names
    assert "network_activity_qa_682" in names


def test_684_685_registry_reconciliation(registry_seed):
    result = ar.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"]}
    assert "coverage_badges_684" in ids
    assert "protocol_directory_685" in ids
    assert result["ok"] is True


# --- API routes ---


def test_api_routes(oml_seed, registry_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/network-activity?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/network-activity/qa-reconciliation?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/asset-registry/coverage?symbol=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/asset-registry/coverage/parity-tests").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/asset-registry/protocols").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/asset-registry/protocols/aave").status_code == 200
