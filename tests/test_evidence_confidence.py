"""Tests — #284 Evidence Confidence Framework (Sprint 2 Intelligence Ledger)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import evidence_confidence as ec


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "evidence_confidence_seed.json"
    seed.write_text(
        json.dumps({
            "calibration": {
                "last_calibration": "2026-08-01",
                "ground_truth_samples": 100,
                "false_positive_rate_pct": 10.0,
                "false_negative_rate_pct": 15.0,
                "bias_detected": False,
                "calibrated": True,
            },
            "assessments": {
                "test-assessment": {
                    "title": "Test research",
                    "conclusion": "Test conclusion",
                    "evidence": {
                        "source_quality": 0.8,
                        "recency": 0.7,
                        "agreement": 0.6,
                        "methodology": 0.9,
                        "completeness": 0.75,
                        "resolution_method": "expert_weighted",
                        "sources": [
                            {"source_id": "a", "conclusion": "bullish", "expert_weight": 0.9},
                            {"source_id": "b", "conclusion": "bearish", "expert_weight": 0.3},
                        ],
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(ec, "_SEED_PATH", seed)
    return seed


def test_formula_documented(isolated_seed):
    formula = ec.build_formula_documentation()
    assert formula["black_box"] is False
    assert formula["weights"]["source_quality"] == 0.30
    assert formula["not_probability_of_price_move"] is True
    assert "30%" in formula["display"]


def test_not_profit_probability(isolated_seed):
    result = ec.build_confidence_assessment("test-assessment")
    assert result["ok"] is True
    assert result["not_profit_probability"] is True
    assert result["ui_label"] == "Confidence in evidence quality"
    assert "not investment outcome" in result["disclaimer"].lower()


def test_reproducible_scoring(isolated_seed):
    evidence = {
        "source_quality": 0.8,
        "recency": 0.7,
        "agreement": 0.6,
        "methodology": 0.9,
        "completeness": 0.75,
        "sources": [],
    }
    score1 = ec.compute_evidence_confidence(evidence)
    score2 = ec.compute_evidence_confidence(evidence)
    assert score1["confidence_score"] == score2["confidence_score"]
    assert score1["reproducible"] is True


def test_contradiction_penalty(isolated_seed):
    sources = [
        {"source_id": "a", "conclusion": "bullish", "expert_weight": 0.9},
        {"source_id": "b", "conclusion": "bearish", "expert_weight": 0.3},
    ]
    penalty = ec.compute_contradiction_penalty(sources)
    assert penalty["contradiction_detected"] is True
    assert penalty["contradiction_penalty"] > 0


def test_no_contradiction_no_penalty(isolated_seed):
    sources = [
        {"source_id": "a", "conclusion": "bullish"},
        {"source_id": "b", "conclusion": "bullish"},
    ]
    penalty = ec.compute_contradiction_penalty(sources)
    assert penalty["contradiction_detected"] is False
    assert penalty["contradiction_penalty"] == 0.0


def test_calibration_tracked(isolated_seed):
    cal = ec.build_calibration_report()
    assert cal["calibration_frequency"] == "monthly"
    assert cal["ground_truth_samples"] == 100
    assert "FP:" in cal["display"]


def test_cross_cutting_status(isolated_seed):
    status = ec.evidence_confidence_status()
    assert status["feature_id"] == 284
    assert status["cross_cutting"] is True
    assert status["acceptance_criteria"]["formula_documented"] is True
    assert status["disclaimer_hideable"] is False


def test_evidence_breakdown(isolated_seed):
    result = ec.build_confidence_assessment("test-assessment")
    conf = result["confidence"]
    assert "weighted_breakdown" in conf
    assert conf["source_count"] == 2
    assert 0 <= conf["confidence_score"] <= 100


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/evidence-confidence/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/evidence-confidence?assessment_id=test-assessment")
    assert resp.status_code == 200
    assert resp.json()["not_profit_probability"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/evidence_confidence_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 284
    assert seed["cross_cutting"] is True
    assert len(seed["assessments"]) >= 2
