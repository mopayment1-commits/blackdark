"""Tests — #408/#459 Smart Money Flow + #461 Beginner Decision Mode + #462 Collateral Grade."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import diligence_risk_scoring as drs
from bd_platform import smart_money_flow_tracker as smf
from bd_platform import unified_arbitrage_engine as uae
import ux_mode


@pytest.fixture
def smf_seed(tmp_path, monkeypatch):
    main = Path("data/smart_money_flow_tracker_seed.json")
    p = tmp_path / "smart_money_flow_tracker_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(smf, "_SEED_PATH", p)
    return p


@pytest.fixture
def drs_seed(tmp_path, monkeypatch):
    main = Path("data/diligence_risk_scoring_seed.json")
    p = tmp_path / "diligence_risk_scoring_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(drs, "_SEED_PATH", p)
    return p


def test_408_status(smf_seed):
    status = smf.smart_money_flow_tracker_status()
    assert status["feature_id"] == 408
    assert status["absorbed_feature_ref"] == 459
    assert status["standalone"] is False


def test_459_dormancy_score(smf_seed):
    btc = smf.compute_dormancy_score("BTC")
    assert btc["ok"] is True
    assert 0 <= btc["dormancy_score"] <= 100
    assert btc["whale_label"] is not None
    assert btc["impact_estimate_pct"] is not None


def test_459_chain_methodology(smf_seed):
    btc_method = smf.get_chain_methodology("bitcoin")
    eth_method = smf.get_chain_methodology("ethereum")
    assert btc_method["model"] == "UTXO"
    assert eth_method["model"] == "Account"


def test_459_transfer_filtering(smf_seed):
    dust = smf.apply_transfer_filters({"amount": 0.00001, "asset": "BTC", "label": ""}, seed=smf._load_seed())
    internal = smf.apply_transfer_filters({"amount": 5, "asset": "BTC", "label": "binance_hot"}, seed=smf._load_seed())
    assert dust["excluded"] is True
    assert internal["excluded"] is True


def test_459_historical_validation(smf_seed):
    validation = smf.build_historical_validation()
    assert validation["validated"] is True


def test_459_reconciliation(smf_seed):
    result = smf.run_reconciliation_tests()
    assert result["ok"] is True


def test_461_beginner_decision_card():
    payload = {
        "verdict": "WAIT",
        "decision_sentence": "Hold and observe",
        "confidence": 0.65,
        "explanation": "Mixed signals",
        "opportunity_score": 55,
        "net_edge_truth": {"truth_score": 72},
    }
    card = ux_mode.build_beginner_decision_card(payload, layer="summary")
    assert card["layer"] == "summary"
    assert card["risk_warning_always_visible"] is True
    assert card["calculations_unchanged"] is True
    assert card["presentation_only"] is True

    details = ux_mode.build_beginner_decision_card(payload, layer="details")
    assert details["truth_score"] == 72
    assert details["expand_to"] == "raw"


def test_461_apply_ux_mode_risk_warning():
    payload = {"verdict": "WAIT", "decision_sentence": "Observe", "confidence": 0.5}
    beginner = ux_mode.apply_ux_mode(payload, mode="beginner")
    assert beginner["risk_warning"]["always_visible"] is True
    assert "decision_card" in beginner


def test_461_status():
    status = ux_mode.beginner_decision_mode_status()
    assert status["feature_ref"] == 461
    assert status["risk_warning_always_visible"] is True


def test_462_collateral_grade(drs_seed):
    eth = drs.score_collateral_risk("ETH")
    assert eth["ok"] is True
    assert eth["collateral_grade"] in ("A", "B", "C", "D", "F")
    assert eth["breakdown"]["no_opaque_score"] is True
    assert "volatility_pct" in eth["breakdown"]
    assert "oracle_health" in eth["breakdown"]


def test_462_defi_scanner_integration():
    opps = uae.scan_defi_opportunities()
    assert len(opps) >= 1
    assert any("collateral_grade_462" in o for o in opps)
