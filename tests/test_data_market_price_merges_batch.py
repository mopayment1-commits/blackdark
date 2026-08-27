"""Tests — #581 Market Metrics, #582 Correlation, #583 Anomaly, #584/#585 Realized Cap."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import data_infrastructure_layer as dil
from bd_platform import flow_to_price_event_correlator as ftpec
from bd_platform import market_anomaly_detection_module as mad
from bd_platform import protocol_valuation_layer as pvl


@pytest.fixture
def dil_seed(tmp_path, monkeypatch):
    main = Path("data/data_infrastructure_layer_seed.json")
    p = tmp_path / "data_infrastructure_layer_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dil, "_SEED_PATH", p)
    return p


@pytest.fixture
def ftpec_seed(tmp_path, monkeypatch):
    main = Path("data/flow_to_price_event_correlator_seed.json")
    p = tmp_path / "flow_to_price_event_correlator_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ftpec, "_SEED_PATH", p)
    return p


@pytest.fixture
def mad_seed(tmp_path, monkeypatch):
    main = Path("data/market_anomaly_detection_seed.json")
    p = tmp_path / "market_anomaly_detection_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(mad, "_SEED_PATH", p)
    return p


@pytest.fixture
def pvl_seed(tmp_path, monkeypatch):
    main = Path("data/protocol_valuation_layer_seed.json")
    p = tmp_path / "protocol_valuation_layer_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pvl, "_SEED_PATH", p)
    return p


# --- #581 ---


def test_581_market_metrics_panel(dil_seed):
    panel = dil.build_price_volume_market_metrics_panel("BTC")
    assert panel["ok"] is True
    assert panel["normalized_feed"]["normalized"] is True


def test_581_source_freshness_visible(dil_seed):
    panel = dil.build_price_volume_market_metrics_panel("BTC")
    prov = panel["source_provenance"]
    assert prov["source_freshness_visible"] is True
    assert prov["source"] is not None


def test_581_stale_feed_handling(dil_seed):
    stale = dil.build_price_volume_market_metrics_panel("STALE")
    assert stale["stale_feed_handling"]["stale"] is True
    assert stale["stale_feed_handling"]["stale_visible"] is True


def test_581_in_infrastructure_panel(dil_seed):
    panel = dil.build_data_infrastructure_panel()
    assert panel["sub_modules"]["581_price_volume_market_metrics"]["ok"] is True


def test_581_reconciliation(dil_seed):
    result = dil.run_reconciliation_tests()
    assert result["all_passed"] is True


# --- #582 ---


def test_582_absorbed_into_556(ftpec_seed):
    panel = ftpec.build_price_move_explanation_panel("btc_move_2026_08_26")
    assert panel["ok"] is True
    assert panel["task_id"] == "582"
    assert panel["not_explanation"] is True


def test_582_evidence_hypothesis_labels(ftpec_seed):
    panel = ftpec.build_price_move_explanation_panel("btc_move_2026_08_26")
    assert "evidence_classification" in panel
    candidates = panel.get("candidate_events_in_window") or []
    if candidates:
        assert candidates[0].get("ui_label") in ("Fact", "Hypothesis", "Inference")


def test_582_no_confidence_causation(ftpec_seed):
    panel = ftpec.build_price_move_explanation_panel("btc_move_2026_08_26")
    metrics = panel.get("metrics") or {}
    assert metrics.get("no_confidence_in_causation") is True


def test_582_unified_epic_panel(ftpec_seed):
    suite = ftpec.build_price_move_event_correlation_layer_panel()
    assert suite["ok"] is True
    assert 582 in suite["feature_ids"]
    assert suite["sub_modules"]["582_asset_general"]["ok"] is True


def test_582_reconciliation(ftpec_seed):
    result = ftpec.run_reconciliation_tests()
    assert result["ok"] is True


# --- #583 ---


def test_583_renamed_module(mad_seed):
    panel = mad.build_market_anomaly_panel("ALT")
    assert panel["legal_name"] == "Market Anomaly Detection Module"
    assert panel["renamed_from"] == "Pump & Dump Detection"


def test_583_multi_signal_gate(mad_seed):
    flagged = mad.detect_market_anomalies("ALT")
    assert flagged["coverage_gate_passed"] is True
    assert len(flagged["signals_detected"]) >= 3


def test_583_statistical_risk_flag(mad_seed):
    flagged = mad.detect_market_anomalies("ALT")
    assert flagged["risk_flag"]["statistical_only"] is True
    assert "Multiple anomalies detected" in flagged["risk_flag"]["display"]


def test_583_below_gate_no_label(mad_seed):
    below = mad.detect_market_anomalies("BTC")
    assert below["risk_flag"] is None


def test_583_reconciliation(mad_seed):
    result = mad.run_reconciliation_tests()
    assert result["ok"] is True


# --- #584/#585 ---


def test_584_realized_cap_panel(pvl_seed):
    panel = pvl.build_realized_cap_panel("bitcoin")
    assert panel["ok"] is True
    assert panel["chain_methodology_documented"] is True


def test_585_entity_adjusted_option(pvl_seed):
    panel = pvl.build_realized_cap_panel("bitcoin", entity_adjusted=True)
    assert panel["entity_adjusted"] is True
    assert panel["entity_adjusted_option"] is True


def test_584_deviations(pvl_seed):
    panel = pvl.build_realized_cap_panel("bitcoin")
    assert "price_vs_realized_pct" in panel["deviations"]


def test_584_in_valuation_panel(pvl_seed):
    panel = pvl.build_protocol_valuation_panel("bitcoin")
    assert panel["sub_modules"]["584_585_realized_cap"]["ok"] is True


def test_584_reconciliation(pvl_seed):
    result = pvl.run_reconciliation_tests()
    assert result["all_passed"] is True
