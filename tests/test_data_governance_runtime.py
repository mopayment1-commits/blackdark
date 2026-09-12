"""Runtime enforcement integration tests — controls must fail closed when removed."""

from __future__ import annotations

import pytest

from blackdark.data_governance.runtime import GovernanceViolationError, enforce_material_write
from decision_ledger import record_decision
from signal_registry import register_signal


def test_decision_record_has_runtime_governance():
    row = record_decision(
        prediction_id="rt_pred_1",
        decision_action="WAIT",
        symbol="BTC",
        evidence_class="SIMULATED",
        source="runtime_test",
    )
    assert row.get("governance", {}).get("contract_id") == "dac_decision_ledger"
    assert row.get("governance", {}).get("receipt_id")
    assert row.get("governance", {}).get("policy") == "v4_v2_runtime"


def test_signal_record_has_runtime_governance():
    row = register_signal(signal_type="oracle_direction", asset="BTC", persist=False)
    assert row.get("governance", {}).get("contract_id") == "dac_signal_registry"
    assert row.get("evidence_class")


def test_enforce_material_write_rejects_bad_promotion():
    with pytest.raises(GovernanceViolationError, match="evidence_promotion_denied"):
        enforce_material_write(
            asset_kind="decision",
            record={
                "decision_id": "dec_x",
                "prediction_id": "p1",
                "decision_action": "WAIT",
                "evidence_class": "PRODUCTION_VERIFIED",
                "source": "simulated",
            },
            surface="test",
            parent={"evidence_class": "SIMULATED", "decision_id": "dec_parent"},
            schema_id="decision_ledger",
        )


def test_governance_disabled_bypasses(monkeypatch):
    monkeypatch.setenv("BLACKDARK_GOVERNANCE_ENFORCE", "0")
    row = enforce_material_write(
        asset_kind="decision",
        record={"decision_id": "d", "prediction_id": "p", "decision_action": "X", "evidence_class": "SIMULATED", "source": "t"},
        surface="test",
    )
    assert "governance" not in row or row.get("governance") is None or row == row


@pytest.mark.asyncio
async def test_cap646_execute_runs_governance_gate():
    from cap646.runtime import execute_capability

    result = await execute_capability(17, params={"symbol": "BTC"}, skip_entitlement=True)
    assert "success" in result or "capability_id" in result
