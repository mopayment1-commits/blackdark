"""Tests — #700 Supply Intelligence, #753 Symbol Mapping, #754/#755 Technical layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import asset_registry as ar
from bd_platform import daily_market_brief as dmb
from bd_platform import investment_thesis_scoring as its
from bd_platform import market_radar_indicators as mri
from bd_platform import on_chain_financials as ocf
from bd_platform import onchain_metrics_library as oml
from bd_platform import reference_data_registry as rdr


@pytest.fixture
def asset_seed(tmp_path, monkeypatch):
    p = tmp_path / "asset_registry_seed.json"
    p.write_text(Path("data/asset_registry_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ar, "_SEED_PATH", p)
    return p


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def rdr_seed(tmp_path, monkeypatch):
    p = tmp_path / "reference_data_registry_seed.json"
    p.write_text(Path("data/reference_data_registry_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(rdr, "_SEED_PATH", p)
    return p


@pytest.fixture
def mri_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_radar_indicators_seed.json"
    p.write_text(Path("data/market_radar_indicators_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(mri, "_SEED_PATH", p)
    return p


# --- #700 Supply Intelligence ---


def test_700_supply_tab_btc(asset_seed):
    tab = ar.build_supply_tab_700(symbol="BTC")
    assert tab["ok"] is True
    assert tab["tab"] == "العرض"
    assert "19.7M" in tab["supply_metadata"]["display"]
    assert tab["supply_metadata"]["mechanism"] == "Mining"


def test_700_supply_tab_eth_deflationary(asset_seed):
    tab = ar.build_supply_tab_700(symbol="ETH")
    assert tab["ok"] is True
    assert tab["supply_metadata"]["max_supply_display"] == "∞"
    assert tab["supply_metadata"]["inflation_pct"] == -0.5


def test_700_supply_reconciliation(asset_seed):
    recon = ar.run_supply_reconciliation_tests_700()
    assert recon["all_passed"] is True


def test_700_dynamic_metrics_eth(oml_seed):
    suite = oml.build_supply_intelligence_metrics_700("ETH")
    assert suite["ok"] is True
    assert suite["supply_change_monthly"] == -12000
    assert suite["deflationary"] is True
    assert "EIP-1559" in (suite.get("context") or "")


def test_700_metrics_library_panel(oml_seed):
    panel = oml.build_metrics_library_panel("ETH")
    assert panel["sub_modules"]["700_supply_intelligence"]["ok"] is True


def test_700_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_supply_change_widget_700("ETH")
    assert widget["widget_label_ar"] == "تغير العرض"
    assert widget["deflationary"] is True


def test_700_thesis_dimension(oml_seed):
    dim = oml.score_supply_mechanics_thesis_dimension_472("ETH")
    assert dim["ok"] is True
    assert dim["dimension"] == "supply_mechanics"
    assert dim["dimension_score"] >= 70


def test_700_daily_brief(oml_seed):
    brief = oml.build_supply_daily_brief_hook_474("ETH")
    assert brief is not None
    assert brief["integration_700"] is True
    assert "deflationary" in brief.get("mention_en", "")


def test_700_regression(oml_seed):
    reg = oml.run_supply_intelligence_regression_tests_700()
    assert reg["deterministic"] is True


# --- #753 Symbol Mapping ---


def test_753_xbt_resolves_btc(rdr_seed):
    resolved = rdr.resolve_symbol_canonical_753("kraken", "XBT")
    assert resolved["ok"] is True
    assert resolved["canonical_id"] == "asset_btc"


def test_753_coingecko_bitcoin(rdr_seed):
    resolved = rdr.resolve_symbol_canonical_753("coingecko", "bitcoin")
    assert resolved["canonical_id"] == "asset_btc"


def test_753_collision_tests(rdr_seed):
    qa = rdr.run_collision_tests_753()
    assert qa["all_passed"] is True


def test_753_version_tests(rdr_seed):
    qa = rdr.run_version_migration_tests_753()
    assert qa["all_passed"] is True


def test_753_coingecko_parity(rdr_seed):
    qa = rdr.run_coingecko_uuid_parity_tests_753()
    assert qa["all_passed"] is True


def test_753_combined_qa(rdr_seed):
    qa = rdr.run_symbol_registry_qa_753()
    assert qa["all_passed"] is True


# --- #754 Technical Indicator Library ---


def test_754_technical_calculation(mri_seed):
    calc = mri.build_technical_calculation_layer_754("BTC")
    assert calc["ok"] is True
    assert calc["indicators"]["RSI"]["value"] is not None
    assert calc["indicators"]["MACD"]["macd"] is not None
    assert len(calc["indicators"]["SMA"]["values"]) == 3
    assert calc["indicators"]["Bollinger"]["upper"] is not None
    assert calc["no_standalone_api"] is True


def test_754_formula_parity(mri_seed):
    parity = mri.run_formula_parity_tests_754()
    assert parity["all_passed"] is True


def test_754_no_look_ahead(mri_seed):
    la = mri.run_look_ahead_tests_754()
    assert la["no_look_ahead"] is True


# --- #755 Technical Summary ---


def test_755_no_strong_buy_sell(mri_seed):
    summary = mri.build_technical_summary_overlay_755("BTC")
    assert summary["ok"] is True
    assert summary["no_strong_buy_sell"] is True
    assert summary["no_rating"] is True
    assert summary["analysis"] in ("Bullish", "Neutral", "Bearish")
    assert "Not financial advice" in summary["disclaimer"]


def test_755_asset_card_panel(mri_seed):
    panel = mri.build_asset_card_indicator_panel_755("BTC")
    assert panel["ok"] is True
    assert panel["panel_name"] == "Indicator Panel"
    assert panel["read_only"] is True
    assert panel["rsi_formula"] is not None


def test_755_market_radar_panel_integration(mri_seed):
    panel = mri.build_market_radar_panel("BTC")
    assert panel["technical_calculation_754"]["ok"] is True
    assert panel["technical_summary_755"]["ok"] is True
    assert panel["supply_change_700"]["ok"] is True


# --- Integrations ---


def test_700_daily_brief_integration(oml_seed):
    brief = dmb.generate_daily_brief()
    assert brief.get("supply_brief_700") is not None


def test_700_thesis_integration(oml_seed):
    thesis = its.score_investment_thesis("ETH")
    assert thesis.get("supply_mechanics_dimension_700") is not None


def test_700_financials_integration(oml_seed):
    panel = ocf.build_on_chain_financials("uniswap")
    ctx = panel.get("supply_tokenomics_700")
    assert ctx is not None
    assert ctx.get("integration_641") is True


def test_api_routes(asset_seed, oml_seed, rdr_seed, mri_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    client = TestClient(app)
    assert client.get("/api/platform/intelligence-ledger/data-layer/asset-registry/supply-tab?symbol=BTC").status_code == 200
    assert client.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/supply-intelligence?asset=ETH").status_code == 200
    assert client.get("/api/platform/internal/reference-data-registry/symbol-registry-qa").status_code == 200
    assert client.get("/api/platform/intelligence-ledger/market-radar/technical-summary?asset=BTC").status_code == 200
    assert client.get("/api/platform/intelligence-ledger/data-layer/asset-registry/indicator-panel?asset=BTC").status_code == 200
