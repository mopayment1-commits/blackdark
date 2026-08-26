"""Tests — #460 Diligence Risk Scoring (Sprint-2 Risk Layer Core)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import diligence_risk_scoring as drs


@pytest.fixture
def drs_seed(tmp_path, monkeypatch):
    main = Path("data/diligence_risk_scoring_seed.json")
    p = tmp_path / "diligence_risk_scoring_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(drs, "_SEED_PATH", p)
    return p


def test_460_status_risk_layer_core(drs_seed):
    status = drs.diligence_risk_scoring_status()
    assert status["feature_id"] == 460
    assert status["standalone"] is False
    assert status["no_opaque_score"] is True
    assert status["weights_documented"] is True
    assert status["evidence_quality_affects_confidence"] is True


def test_460_transparent_breakdown(drs_seed):
    result = drs.score_entity_risk("BTC")
    assert result["ok"] is True
    assert result["no_opaque_score"] is True
    assert result["weights_documented"] is True
    assert result["scoring_engine_version"] == "1.0.0"
    assert "asset_diligence" in result["category_scores"]
    breakdown = result["category_scores"]["asset_diligence"]["findings_breakdown"]
    assert len(breakdown) >= 1
    assert "evidence_confidence" in breakdown[0]
    assert "adjusted_risk_points" in breakdown[0]


def test_460_category_weights_documented(drs_seed):
    result = drs.score_entity_risk("ETH")
    weights = result["category_weights"]
    assert abs(sum(weights.values()) - 1.0) < 0.01
    assert set(weights.keys()) == {"asset_diligence", "collateral_risk", "correlation_risk", "venue_diligence"}


def test_460_evidence_quality_reduces_confidence(drs_seed):
    uni = drs.score_entity_risk("UNI")
    col = uni["category_scores"]["collateral_risk"]
    low_ev = [f for f in col["findings_breakdown"] if f["evidence_quality"] == "low"]
    assert len(low_ev) >= 1
    assert low_ev[0]["evidence_confidence"] == 0.5
    assert col["confidence"] < 0.9


def test_462_collateral_risk_shared_engine(drs_seed):
    result = drs.score_collateral_risk("ETH")
    assert result["ok"] is True
    assert result["feature_ref"] == 462
    assert result["category"] == "collateral_risk"
    assert result["no_opaque_score"] is True


def test_463_correlation_risk_shared_engine(drs_seed):
    result = drs.score_correlation_risk("ETH")
    assert result["ok"] is True
    assert result["feature_ref"] == 463
    assert result["category"] == "correlation_risk"


def test_417_net_edge_ranking_integration(drs_seed):
    ranking = drs.rank_opportunities()
    assert ranking["count"] >= 2
    top = ranking["ranked_opportunities"][0]
    assert "final_rank_score" in top["ranking"]
    assert top["net_edge_truth"]["feature_ref"] == 417
    assert top["no_opaque_score"] is True


def test_417_risk_penalizes_higher_risk_asset(drs_seed):
    ranking = drs.rank_opportunities()
    scores = {r["asset"]: r["ranking"]["final_rank_score"] for r in ranking["ranked_opportunities"]}
    assert scores["BTC"] > scores["UNI"]


def test_460_net_edge_truth_wrapper(drs_seed):
    from net_edge_truth import rank_opportunity_with_diligence_risk

    opp = {
        "opportunity_id": "test",
        "asset": "BTC",
        "net_profit_usdt": 1.0,
        "total_slippage_bps": 10.0,
        "trading_fees_usdt": 0.1,
        "withdrawal_fee_usdt": 0.2,
        "quote_age_ms": 400,
    }
    result = rank_opportunity_with_diligence_risk(opp)
    assert result["ok"] is True
    assert result["ranking"]["final_rank_score"] > 0


def test_460_panel(drs_seed):
    panel = drs.build_risk_scoring_panel("BTC")
    assert panel["ok"] is True
    assert panel["collateral_risk"]["feature_ref"] == 462
    assert panel["correlation_risk"]["feature_ref"] == 463


def test_460_reconciliation(drs_seed):
    result = drs.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
