"""Tests — Flow-to-Price Event Correlator #556."""

from __future__ import annotations

import json

import pytest

from bd_platform import flow_to_price_event_correlator as ftpec


@pytest.fixture
def flow_correlator_seed(tmp_path, monkeypatch):
    p = tmp_path / "flow_to_price_event_correlator_seed.json"
    p.write_text(json.dumps({
        "price_events": {
            "test_move": {
                "asset": "BTC",
                "timestamp": "2026-08-26T14:00:00Z",
                "price_change_pct": -3.2,
                "correlation_window_seconds": 3600,
            },
        },
        "flow_events": {
            "BTC": [
                {
                    "event_id": "f1",
                    "category": "whale_flow",
                    "description": "Whale transfer to exchange",
                    "timestamp": "2026-08-26T13:50:00Z",
                    "value_usd": 25000000.0,
                    "source": "entity_layer",
                    "evidence_id": "ev-001",
                    "evidence_link": "/test/ev-001",
                    "data_completeness_pct": 90.0,
                },
                {
                    "event_id": "f2",
                    "category": "derivatives",
                    "description": "Liquidation cascade",
                    "timestamp": "2026-08-26T13:55:00Z",
                    "value_usd": 120000000.0,
                    "source": "derivatives_feed",
                    "evidence_id": "ev-002",
                    "evidence_link": "/test/ev-002",
                    "data_completeness_pct": 88.0,
                },
                {
                    "event_id": "f3",
                    "category": "exchange_flow",
                    "description": "Exchange inflow",
                    "timestamp": "2026-08-26T10:00:00Z",
                    "value_usd": 5000000.0,
                    "source": "exchange_layer",
                    "evidence_id": "ev-003",
                    "data_completeness_pct": 95.0,
                },
            ],
        },
    }), encoding="utf-8")
    monkeypatch.setattr(ftpec, "_SEED_PATH", p)
    return p


def test_status_renamed_not_explanation_engine(flow_correlator_seed):
    status = ftpec.flow_to_price_event_correlator_status()
    assert status["renamed_from"] == "Flow-to-Price Explanation Engine"
    assert status["not_explanation_engine"] is True
    assert status["correlation_not_causation"] is True


def test_candidate_events_not_likely_drivers(flow_correlator_seed):
    panel = ftpec.build_flow_to_price_event_correlator_panel(event_id="test_move")
    assert panel["ok"] is True
    assert panel["candidate_count"] == 2
    assert "likely drivers" in panel["banned_output_terms"]
    for c in panel["candidate_events_in_window"]:
        assert c["correlation_not_causation"] is True
        assert c["causation_unverified"] is True


def test_hypothesis_labels_with_alternatives(flow_correlator_seed):
    panel = ftpec.build_flow_to_price_event_correlator_panel(event_id="test_move")
    hypotheses = panel["competing_hypotheses"]
    assert len(hypotheses) >= 2
    assert panel["alternatives_always_shown"] is True
    assert panel["hypothesis_labels"] is True
    for h in hypotheses:
        assert "Hypothesis" in h["hypothesis_label"]
        assert h["causation_unverified"] is True
        assert "Causation: Unverified" in h["display"]


def test_evidence_strength_not_confidence(flow_correlator_seed):
    panel = ftpec.build_flow_to_price_event_correlator_panel(event_id="test_move")
    for c in panel["candidate_events_in_window"]:
        assert c["evidence_strength_not_confidence"] is True
    assert panel["metrics"]["no_confidence_pct_for_causation"] is True


def test_correlation_not_causation_explicit(flow_correlator_seed):
    panel = ftpec.build_flow_to_price_event_correlator_panel(event_id="test_move")
    assert panel["correlation_not_causation_explicit"] is True
    assert "Causation: Unverified" in panel["summary_display"]


def test_timestamps_aligned_and_evidence_links(flow_correlator_seed):
    panel = ftpec.build_flow_to_price_event_correlator_panel(event_id="test_move")
    assert panel["timestamps_aligned"] is True
    assert len(panel["evidence_links"]) >= 2


def test_metrics_data_completeness_not_confidence(flow_correlator_seed):
    panel = ftpec.build_flow_to_price_event_correlator_panel(event_id="test_move")
    assert "data_completeness_pct" in panel["metrics"]
    assert "temporal_alignment_seconds" in panel["metrics"]
