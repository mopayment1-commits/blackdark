"""Runtime governance enforcement — fail-closed material write gates (R1)."""

from __future__ import annotations

import os

import pytest

from blackdark.data_governance.runtime import (
    GovernanceViolationError,
    enforce_material_write,
    governance_enforce_enabled,
    require_capability_dna,
)
from cap646.evidence_class import assert_promotion_allowed


def test_governance_default_enforce_on():
    assert governance_enforce_enabled() is True


def test_governance_cannot_disable_in_production(monkeypatch):
    monkeypatch.setenv("BLACKDARK_GOVERNANCE_ENFORCE", "0")
    monkeypatch.setenv("APP_ENV", "production")
    assert governance_enforce_enabled() is True


def test_decision_write_attaches_intelligence_receipt():
    row = enforce_material_write(
        "decision",
        {
            "decision_id": "dec_test",
            "prediction_id": "pred_test",
            "symbol": "BTC",
            "source": "oracle",
            "evidence_class": "SHADOW_LIVE_FORWARD",
        },
    )
    assert row.get("governance_enforced") is True
    assert "intelligence_receipt" in row
    assert row["intelligence_receipt"]["receipt_hash"]


def test_decision_requires_capability_dna_when_enforced():
    with pytest.raises(GovernanceViolationError, match="capability_dna"):
        require_capability_dna({"decision_id": "x"}, surface="decision")


def test_rights_denied_blocks_material_write(monkeypatch):
    monkeypatch.setenv("BLACKDARK_GOVERNANCE_ENFORCE", "1")
    with pytest.raises(GovernanceViolationError, match="rights_denied"):
        enforce_material_write(
            "signal",
            {
                "signal_type": "test",
                "asset": "BTC",
                "source_id": "nonexistent_vendor_xyz",
                "purpose": "live_trading",
            },
        )


def test_evidence_promotion_blocked_simulated_to_production():
    with pytest.raises(ValueError, match="evidence_promotion_denied"):
        assert_promotion_allowed("SIMULATED", "PRODUCTION_VERIFIED")


def test_record_decision_calls_runtime_gate():
    from decision_ledger import record_decision

    row = record_decision(
        prediction_id="pred_rt_1",
        decision_action="hold",
        symbol="BTC",
        source="oracle",
    )
    assert row.get("governance_enforced") is True
    assert row.get("capability_dna")
    assert row.get("intelligence_receipt")


def test_register_signal_calls_runtime_gate():
    from signal_registry import register_signal

    row = register_signal(signal_type="oracle_direction", asset="ETH", persist=False)
    assert row.get("governance_enforced") is True


def test_oracle_chain_calls_runtime_gate(tmp_path, monkeypatch):
    import oracle_audit_chain as chain

    monkeypatch.setattr(chain, "CHAIN_PATH", tmp_path / "chain.jsonl")
    entry = chain.append_prediction_record({"prediction_id": "p1", "symbol": "BTC", "source": "oracle"})
    assert entry.get("governance_enforced") is True


def test_runtime_removal_fails_decision_path(monkeypatch):
    """R1 — test must fail if control removed."""
    import decision_ledger as dl

    def _bypass(*_a, **_k):
        raise RuntimeError("governance_bypass_detected")

    monkeypatch.setattr(
        "blackdark.data_governance.runtime.enforce_material_write",
        _bypass,
    )
    with pytest.raises(RuntimeError, match="governance_bypass"):
        dl.record_decision(
            prediction_id="pred_fail",
            decision_action="hold",
            symbol="BTC",
        )
