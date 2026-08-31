"""Tests — #316 Epistemic Output Framework."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import epistemic_output_framework as eof


@pytest.fixture
def epistemic_seed(tmp_path, monkeypatch):
    p = tmp_path / "epistemic_output_framework_seed.json"
    p.write_text(json.dumps({
        "panels": {
            "test_panel": {
                "title": "Test",
                "asset": "BTC",
                "analysis_summary": "Cross-domain analysis only — user decides.",
                "domain_signals": [
                    {"domain": "derivatives", "direction": "bullish"},
                    {"domain": "sentiment", "direction": "bearish"},
                ],
                "epistemic_items": [
                    {
                        "epistemic_type": "fact",
                        "statement": "BTC funding rate is negative",
                        "verified": True,
                        "evidence": [{"evidence_id": "e1", "source": "Binance"}],
                    },
                    {
                        "epistemic_type": "inference",
                        "statement": "Positioning diverges from sentiment",
                        "confidence_pct": 75,
                        "supporting_fact_refs": ["e1"],
                        "evidence": [{"evidence_id": "e2"}],
                    },
                    {
                        "epistemic_type": "hypothesis",
                        "statement": "Short squeeze risk may rise if funding stays negative",
                        "probability_range_pct": [30, 50],
                        "test_conditions": ["7 days negative funding"],
                        "evidence": [{"evidence_id": "e3"}],
                    },
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(eof, "_SEED_PATH", p)
    return p


def test_316_epistemic_separation(epistemic_seed):
    panel = eof.build_cross_domain_panel("test_panel")
    output = panel["output"]
    assert output["not_decision"] is True
    assert output["evidence"]["fact_count"] == 1
    assert output["evidence"]["inference_count"] == 1
    assert output["evidence"]["hypothesis_count"] == 1
    assert output["evidence"]["epistemic_separation"] is True


def test_316_no_decision_language(epistemic_seed):
    check = eof.validate_no_decision_language("Analysis shows accumulation patterns")
    assert check["valid"] is True

    bad = eof.validate_no_decision_language("We recommend you buy BTC now")
    assert bad["valid"] is False
    assert "buy" in bad["violations"]


def test_316_traceability(epistemic_seed):
    chain = [eof.build_evidence_link(evidence_id="e1", provenance_metric_id="spot.btc.price")]
    fact = eof.build_fact("BTC price is 65000", evidence_chain=chain, verified=True)
    assert fact["evidence_trace_hash"]
    assert fact["confidence"]["value_pct"] == 100.0
    assert "/provenance-lineage/audit/" in chain[0]["provenance_audit_path"]


def test_316_confidence_taxonomy():
    inf = eof.build_inference(
        "Test inference",
        supporting_facts=[{"ref": "f1"}],
        confidence_pct=72,
        evidence_chain=[{"evidence_id": "e1"}],
    )
    assert inf["confidence"]["supporting_facts_count"] == 1

    hyp = eof.build_hypothesis(
        "Test hypothesis",
        probability_range=(30, 55),
        test_conditions=["condition A"],
        evidence_chain=[{"evidence_id": "e1"}],
    )
    assert hyp["confidence"]["probability_range_pct"] == [30.0, 55.0]


def test_316_confirm_contradict_no_decision():
    signals = [
        {"domain": "derivatives", "direction": "bullish"},
        {"domain": "market_state", "direction": "bullish"},
        {"domain": "sentiment", "direction": "bearish"},
    ]
    result = eof.confirm_contradict_domains(signals)
    assert result["no_decision_output"] is True
    assert len(result["confirming_pairs"]) >= 1
    assert len(result["contradicting_pairs"]) >= 1


def test_316_fact_requires_evidence():
    with pytest.raises(ValueError, match="evidence"):
        eof.build_fact("No evidence", evidence_chain=[])


def test_316_status(epistemic_seed):
    status = eof.epistemic_output_framework_status()
    assert status["feature_id"] == 316
    assert status["renamed_from"] == "Cross-Domain Decision Intelligence"
    assert status["design_principle"] is True
    assert status["acceptance_criteria"]["ai_ml_never_fact"] is True


def test_api_routes(epistemic_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/epistemic-output/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/epistemic-output?panel_id=test_panel")
    assert resp.status_code == 200
    assert resp.json()["output"]["not_decision"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/epistemic_output_framework_seed.json").read_text())
    assert seed["feature_id"] == 316
    assert seed["title"] == "Epistemic Output Framework"
