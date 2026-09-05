"""Tests — Epistemic Humility Gate (Sprint 2 Intelligence Ledger)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import epistemic_humility_gate as gate


@pytest.fixture
def gate_seed() -> dict:
    return json.loads(Path("data/epistemic_humility_gate_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    gate.reset_epistemic_gate_state()
    yield
    gate.reset_epistemic_gate_state()


def test_gate_status_no_standalone(gate_seed):
    status = gate.epistemic_gate_status(seed=gate_seed)
    assert status["standalone_rejected"] is True
    assert status["sprint"] == 2
    assert status["surface"] == "/intelligence/gate"
    assert status["policy"]["rule_based_only"] is True
    assert status["policy"]["no_ml_gate_logic"] is True
    assert status["policy"]["confidence_min"] == 5.0
    assert status["policy"]["sample_size_min"] == 30


def test_public_methodology_transparent(gate_seed):
    methodology = gate.get_public_methodology(seed=gate_seed)
    codes = {t["code"] for t in methodology["triggers"]}
    assert codes == {"CONFLICT", "LOW_CONFIDENCE", "INSUFFICIENT_DATA", "STALE_DATA"}


def test_conflict_detection_quantifiable(gate_seed):
    conflict = gate.detect_evidence_conflict(100.0, 130.0, seed=gate_seed)
    assert conflict["conflict"] is True
    assert conflict["reason_code"] == "CONFLICT"
    assert conflict["delta_pct"] > 15.0

    ok = gate.detect_evidence_conflict(100.0, 110.0, seed=gate_seed)
    assert ok["conflict"] is False


def test_low_confidence_trigger(gate_seed):
    result = gate.check_confidence_threshold(3.0, seed=gate_seed)
    assert result["ok"] is False
    assert result["reason_code"] == "LOW_CONFIDENCE"


def test_insufficient_data_trigger(gate_seed):
    result = gate.check_sample_size(12, seed=gate_seed)
    assert result["ok"] is False
    assert result["reason_code"] == "INSUFFICIENT_DATA"


def test_stale_data_trigger(gate_seed):
    result = gate.check_stale_data(48.0, seed=gate_seed)
    assert result["ok"] is False
    assert result["reason_code"] == "STALE_DATA"


def test_idk_output_with_disclaimer(gate_seed):
    out = gate.build_idk_output(
        reason_code="CONFLICT",
        evidence_summary=[{"source": "oracle", "value": 100}],
        missing_data=["reconciled_evidence"],
        seed=gate_seed,
    )
    assert out["output"] == "I DON'T KNOW"
    assert out["reason_code"] == "CONFLICT"
    assert out["no_buy_sell"] is True
    assert "بيانات غير كافية" in out["disclaimer_ar"]


def test_gate_passes_with_sufficient_evidence(gate_seed):
    result = gate.evaluate_epistemic_gate(
        asset="BTC",
        confidence_score=8.0,
        sample_size=120,
        fact_a=100.0,
        fact_b=105.0,
        data_age_hours=2.0,
        evidence=[{"source": "binance"}, {"source": "dexscreener"}],
        user_tier="pro",
        seed=gate_seed,
    )
    assert result["gate_passed"] is True
    assert result["abstained"] is False
    assert result["fee_db"]["fee_db_logged"] is True
    assert result["fee_db"]["user_tier"] == "pro"


def test_gate_abstains_on_conflict(gate_seed):
    result = gate.evaluate_epistemic_gate(
        asset="ETH",
        confidence_score=8.0,
        sample_size=100,
        fact_a=100.0,
        fact_b=200.0,
        seed=gate_seed,
    )
    assert result["abstained"] is True
    assert result["result"]["output"] == "I DON'T KNOW"
    assert result["result"]["reason_code"] == "CONFLICT"
    assert result["signal_engine"]["publish_allowed"] is False
    assert result["accuracy_ledger"] is not None
    assert "Blocked" in result["provenance"]["footer_note"]


def test_gate_abstains_low_confidence(gate_seed):
    result = gate.evaluate_epistemic_gate(
        asset="SOL",
        confidence_score=2.5,
        sample_size=50,
        seed=gate_seed,
    )
    assert result["abstained"] is True
    assert result["result"]["reason_code"] == "LOW_CONFIDENCE"


def test_fee_db_logged_every_evaluation(gate_seed):
    gate.evaluate_epistemic_gate(asset="BTC", confidence_score=7.0, sample_size=50, seed=gate_seed)
    gate.evaluate_epistemic_gate(asset="ETH", confidence_score=2.0, sample_size=10, seed=gate_seed)
    panel = gate.get_gate_hit_rate_panel(seed=gate_seed)
    assert panel["total_evaluations"] == 2
    assert panel["abstentions"] == 1


def test_hit_rate_panel_target(gate_seed):
    for _ in range(3):
        gate.evaluate_epistemic_gate(asset="BTC", confidence_score=2.0, sample_size=10, seed=gate_seed)
    for _ in range(7):
        gate.evaluate_epistemic_gate(asset="BTC", confidence_score=8.0, sample_size=100, seed=gate_seed)
    panel = gate.get_gate_hit_rate_panel(seed=gate_seed)
    assert panel["abstention_rate_pct"] == 30.0
    assert panel["target_pct"]["min"] == 20
    assert panel["target_pct"]["max"] == 40


def test_signal_publish_blocked_on_abstain(gate_seed):
    result = gate.gate_signal_before_publish(
        asset="BTC",
        confidence_score=1.0,
        sample_size=5,
        seed=gate_seed,
    )
    assert result["publish_allowed"] is False


def test_e2e_all_checks(gate_seed):
    e2e = gate.run_epistemic_gate_e2e(seed=gate_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
