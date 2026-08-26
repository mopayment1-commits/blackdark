"""Tests — #315 Derivatives Cross-Signal Synthesis Module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bd_platform import derivatives_cross_signal_synthesis as dcs


@pytest.fixture
def synthesis_seed(tmp_path, monkeypatch):
    p = tmp_path / "derivatives_cross_signal_synthesis_seed.json"
    p.write_text(json.dumps({
        "backtest": {
            "historical_events_tested": 50,
            "true_positive_rate_pct": 75,
            "false_positive_rate_pct": 18,
            "contradiction_latency_minutes": 10,
            "brier_score": 0.18,
        },
        "assets": {
            "BTC": {
                "timeframes": {
                    "4h": {
                        "signals": [
                            {"signal_id": "funding", "signal_type": "funding", "value": 0.001,
                             "available": True, "rolling_30d": {"mean": 0.0001, "std": 0.0001},
                             "freshness_score": 0.9, "source_quality_score": 0.9, "historical_accuracy_score": 0.8},
                            {"signal_id": "open_interest", "signal_type": "oi", "value": 10,
                             "available": True, "rolling_30d": {"mean": 2, "std": 3},
                             "freshness_score": 0.9, "source_quality_score": 0.9, "historical_accuracy_score": 0.8},
                            {"signal_id": "cvd_flow", "signal_type": "cvd", "value": 3,
                             "available": True, "rolling_30d": {"mean": 0, "std": 1},
                             "freshness_score": 0.9, "source_quality_score": 0.9, "historical_accuracy_score": 0.8},
                            {"signal_id": "liquidations", "signal_type": "liq", "value": -3,
                             "available": True, "rolling_30d": {"mean": 0, "std": 1},
                             "freshness_score": 0.9, "source_quality_score": 0.9, "historical_accuracy_score": 0.8},
                        ],
                    },
                    "1h": {
                        "signals": [
                            {"signal_id": "funding", "value": 0.001, "available": True,
                             "rolling_30d": {"mean": 0, "std": 1},
                             "freshness_score": 0.9, "source_quality_score": 0.9, "historical_accuracy_score": 0.8},
                            {"signal_id": "oi", "value": 5, "available": True,
                             "rolling_30d": {"mean": 0, "std": 1},
                             "freshness_score": 0.9, "source_quality_score": 0.9, "historical_accuracy_score": 0.8},
                        ],
                    },
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(dcs, "_SEED_PATH", p)
    return p


@pytest.fixture
def mock_market_state():
    with patch.object(dcs, "check_market_state_dependency", return_value={"stable": True, "required_feature_id": 327}):
        yield


def test_315_renamed_no_decision(synthesis_seed):
    status = dcs.derivatives_cross_signal_synthesis_status()
    assert status["renamed_from"] == "Cross-Derivatives Decision Intelligence"
    assert status["title"] == "Derivatives Cross-Signal Synthesis Module"
    assert status["requires_feature_id"] == 327


def test_315_agreement_detection(synthesis_seed):
    signals = [
        {"direction": "bullish"}, {"direction": "bullish"},
        {"direction": "bullish"}, {"direction": "bullish"},
    ]
    result = dcs.detect_agreement(signals)
    assert result["agreement_level"] == "convergent"
    assert result["no_decision_output"] is True


def test_315_min_signals_enforced(synthesis_seed, mock_market_state):
    result = dcs.build_cross_signal_synthesis_panel("BTC", timeframe="1h")
    assert result["ok"] is False
    assert result["error"] == "insufficient_signals"
    assert result["output"] is None
    assert result["min_required"] == 3


def test_315_full_panel(synthesis_seed, mock_market_state):
    panel = dcs.build_cross_signal_synthesis_panel("BTC", timeframe="4h")
    assert panel["ok"] is True
    assert panel["not_decision_intelligence"] is True
    assert "signal_agreement_matrix" in panel
    assert "contradiction_flags" in panel
    assert "confidence_score" in panel
    assert panel["language_check"]["valid"] is True


def test_315_forbidden_language():
    bad = dcs.validate_no_forbidden_language("This is a decision to buy")
    assert bad["valid"] is False
    assert "decision" in bad["violations"]


def test_315_matrix_evidence_chain(synthesis_seed, mock_market_state):
    panel = dcs.build_cross_signal_synthesis_panel("BTC", timeframe="4h")
    cell = panel["signal_agreement_matrix"]["matrix"][0]
    assert cell["badge"]["clickable"] is True
    assert cell["epistemic"]["epistemic_framework_feature_id"] == 316


def test_315_backtest_gates(synthesis_seed):
    bt = dcs.build_backtest_acceptance()
    assert bt["gates_passed"] is True
    assert bt["agreement_tp_gate"] is True
    assert bt["agreement_fp_gate"] is True


def test_315_root_cause_categories(synthesis_seed):
    bullish = [{"signal_id": "funding", "z_score": 2.5}]
    bearish = [{"signal_id": "open_interest", "z_score": -2.5}]
    cause = dcs._classify_root_cause(bullish, bearish)
    assert cause in dcs._ROOT_CAUSE_CATEGORIES
    assert len(dcs._ROOT_CAUSE_CATEGORIES) >= 5


def test_api_routes(synthesis_seed, mock_market_state):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/derivatives-cross-signal/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/derivatives-cross-signal?asset=BTC&timeframe=4h").status_code == 200
    insufficient = c.get("/api/platform/intelligence-ledger/derivatives-cross-signal?asset=BTC&timeframe=1h")
    assert insufficient.status_code == 200
    assert insufficient.json()["error"] == "insufficient_signals"


def test_full_seed_exists():
    seed = json.loads(Path("data/derivatives_cross_signal_synthesis_seed.json").read_text())
    assert seed["feature_id"] == 315
    assert seed["requires_feature_id"] == 327
