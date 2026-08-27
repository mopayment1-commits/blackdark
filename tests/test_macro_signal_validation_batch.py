"""Tests — #774 Macro Coupling, #776 Signal Validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import market_radar_indicators as mri
from bd_platform import signal_validation_layer as svl


@pytest.fixture
def mri_seed():
    return json.loads(Path("data/market_radar_indicators_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def svl_seed():
    return json.loads(Path("data/signal_validation_layer_seed.json").read_text(encoding="utf-8"))


# --- #774 ---


def test_774_formula_documented(mri_seed):
    overlay = mri.build_btc_macro_coupling_overlay_774("BTC", seed=mri_seed)
    assert overlay["ok"] is True
    assert overlay["windows_documented"] == ["30D", "90D", "1Y"]
    assert len(overlay["macro_factors"]) == 5


def test_774_dxy_output_format(mri_seed):
    overlay = mri.build_btc_macro_coupling_overlay_774("BTC", seed=mri_seed)
    display = overlay["display"]
    assert "BTC-DXY Correlation (90D):" in display
    assert "p-value:" in display
    assert "Window:" in display
    assert overlay["no_macro_score"] is True


def test_774_significance_shown(mri_seed):
    coupling = mri.compute_macro_coupling_factor_774("BTC", "DXY", window="90D", seed=mri_seed)
    assert coupling["significance_shown"] is True
    assert coupling["p_value"] is not None


def test_774_disclaimer(mri_seed):
    overlay = mri.build_btc_macro_coupling_overlay_774("BTC", seed=mri_seed)
    assert overlay["disclaimer_non_hideable"] is True
    assert "Not causation" in overlay["disclaimer"]


def test_774_no_prediction(mri_seed):
    overlay = mri.build_btc_macro_coupling_overlay_774("BTC", seed=mri_seed)
    assert overlay["no_prediction"] is True
    assert overlay["historical_only"] is True


def test_774_qa_tolerance(mri_seed):
    qa = mri.run_macro_coupling_qa_774("BTC", seed=mri_seed)
    assert qa["all_passed"] is True
    assert qa["tolerance"] == 0.01


def test_774_market_radar_widget(mri_seed):
    widget = mri.build_market_radar_macro_coupling_widget_774("BTC", seed=mri_seed)
    assert widget["widget_label_ar"] == "السياق الماكرو"


def test_774_asset_card(mri_seed):
    card = mri.build_asset_card_macro_coupling_774("BTC", seed=mri_seed)
    assert card["tab_ar"] == "الارتباط الماكرو"


def test_774_market_radar_panel(mri_seed):
    panel = mri.build_market_radar_panel("binance", "BTC", seed=mri_seed)
    assert panel["macro_coupling_774"]["ok"] is True


# --- #776 ---


def test_776_validation_statuses(svl_seed):
    panel = svl.build_signal_validation_panel_776("BTC", seed=svl_seed)
    assert panel["ok"] is True
    assert panel["validation_status"] in ("Confirmed", "Mixed", "Contradictory")


def test_776_three_domains(svl_seed):
    panel = svl.build_signal_validation_panel_776("BTC", seed=svl_seed)
    domains = [s["domain"] for s in panel["signals"]]
    assert "Technical" in domains
    assert "On-Chain" in domains
    assert "Sentiment" in domains


def test_776_no_forced_consensus(svl_seed):
    panel = svl.build_signal_validation_panel_776("BTC", seed=svl_seed)
    assert panel["no_forced_consensus"] is True
    assert panel["no_trading_signal"] is True
    assert panel["no_execution"] is True


def test_776_conflicts_explained(svl_seed):
    panel = svl.build_signal_validation_panel_776("BTC", seed=svl_seed)
    if panel["validation_status"] == "Contradictory":
        assert panel["conflicts"]
        assert "التعارض" in panel["display"]


def test_776_citations_per_signal(svl_seed):
    panel = svl.build_signal_validation_panel_776("BTC", seed=svl_seed)
    for signal in panel["signals"]:
        assert "citation" in signal
        assert "Source:" in signal["citation"]


def test_776_next_actions_no_trade(svl_seed):
    panel = svl.build_signal_validation_panel_776("BTC", seed=svl_seed)
    for action in panel["next_analytical_actions"]:
        assert "Buy" not in action["label_ar"]
        assert "Sell" not in action["label_ar"]
        assert "route" in action


def test_776_signal_card(svl_seed):
    card = svl.build_signal_card_cross_validation_776("BTC", seed=svl_seed)
    assert card["panel_title_ar"] == "التحقق المتقاطع"
    assert card["expandable"] is True


def test_776_ledger_hook(svl_seed):
    ledger = svl.build_intelligence_ledger_signal_quality_776("BTC", seed=svl_seed)
    assert ledger["dimension"] == "signal_quality_scoring"


def test_776_qa_suite(svl_seed):
    qa = svl.run_signal_validation_qa_776(seed=svl_seed)
    assert qa["all_passed"] is True
