"""Tests — #281 Order Book Pattern Recognition Engine (renamed, no financial claims)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import order_book_pattern_recognition as obpr


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "order_book_pattern_recognition_seed.json"
    seed.write_text(
        json.dumps({
            "compliance": {
                "legal_review_complete": False,
                "rule_based_months_validated": 2,
            },
            "backtest": {
                "years": 2,
                "start_date": "2024-08-25",
                "end_date": "2026-08-25",
                "pattern_count": 5,
                "walk_forward_folds": 4,
                "historical_metrics": {"pattern_match_rate_pct": 60.0},
            },
            "patterns": {
                "BTC": [
                    {
                        "pattern_id": "obpr-001",
                        "pattern_name": "Bid wall absorption",
                        "pattern_match_score": 0.78,
                        "phase": "rule_based",
                        "feature_count": 24,
                        "backtest_window_years": 2,
                        "explainability_reasons": ["Bid depth 3.2σ above baseline"],
                    },
                    {
                        "pattern_id": "obpr-ml",
                        "pattern_name": "ML pattern (blocked)",
                        "pattern_match_score": 0.9,
                        "phase": "ml_augmentation",
                        "feature_count": 100,
                    },
                ],
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(obpr, "_SEED_PATH", seed)
    return seed


def test_renamed_not_intelligence_ai(isolated_seed):
    status = obpr.pattern_recognition_status()
    assert status["feature_id"] == 281
    assert "Pattern Recognition" in status["title"]
    assert status["renamed_from"] == "Order Book Intelligence AI/ML"


def test_financial_claims_banned(isolated_seed):
    criteria = obpr.build_acceptance_criteria()
    assert criteria["sharpe_claims_banned"] is True
    assert criteria["drawdown_claims_banned"] is True
    assert criteria["win_rate_claims_banned"] is True
    assert criteria["no_forward_performance_guarantee"] is True
    assert "No Sharpe" in criteria["display"]
    assert "≥1.5" not in criteria["display"]


def test_compliance_gate_blocks_ml(isolated_seed):
    gate = obpr.build_compliance_gate()
    assert gate["ml_blocked_until_compliance"] is True
    assert gate["legal_review_complete"] is False
    assert gate["current_phase"] == "rule_based"


def test_pattern_match_not_signal(isolated_seed):
    panel = obpr.build_pattern_recognition_panel("BTC")
    assert panel["ok"] is True
    assert panel["not_trading_signals"] is True
    assert panel["output_type"] == "historical_pattern_match"
    match = panel["pattern_matches"][0]
    assert match["not_a_signal"] is True
    assert match["not_a_recommendation"] is True
    assert "not profit probability" in match["pattern_match_score_label"]
    assert "Sharpe" not in match["display"]


def test_ml_patterns_filtered_when_blocked(isolated_seed):
    panel = obpr.build_pattern_recognition_panel("BTC")
    phases = [m["phase"] for m in panel["pattern_matches"]]
    assert "ml_augmentation" not in phases


def test_explainability_reasons(isolated_seed):
    panel = obpr.build_pattern_recognition_panel("BTC")
    match = panel["pattern_matches"][0]
    assert len(match["explainability_reasons"]) >= 1


def test_backtest_historical_only(isolated_seed):
    backtest = obpr.build_backtest_documentation()
    assert backtest["years"] == 2
    assert backtest["historical_only"] is True
    assert backtest["no_forward_guarantee"] is True


def test_mandatory_disclaimer(isolated_seed):
    status = obpr.pattern_recognition_status()
    assert status["disclaimer_hideable"] is False
    assert "Past performance does not indicate future results" in status["disclaimer"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/pattern-recognition/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/pattern-recognition?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["not_trading_signals"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/order_book_pattern_recognition_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 281
    assert seed["compliance"]["ml_augmentation_blocked"] is True
    assert seed["backtest"]["years"] >= 2
