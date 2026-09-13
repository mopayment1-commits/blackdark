"""DSR / D-domain closure tests — per-requirement R1 control removal guards."""

from __future__ import annotations

import pytest

from blackdark.data_governance.runtime import GovernanceViolationError, enforce_material_write

_BASE = {
    "signal_type": "test",
    "asset": "BTC",
    "source_id": "internal_cache",
    "purpose": "analytics",
}

DSR_PARTIAL_IDS = (
    "DSR-001",
    "DSR-002",
    "DSR-003",
    "DSR-004",
    "DSR-006",
    "DSR-007",
    "DSR-009",
    "DSR-010",
    "DSR-011",
    "DSR-014",
    "DSR-015",
    "DSR-017",
    "DSR-018",
    "DSR-019",
    "DSR-020",
    "DSR-021",
    "DSR-022",
    "DSR-023",
    "DSR-024",
)

D_PARTIAL_IDS = (
    "D-01",
    "D-02",
    "D-03",
    "D-04",
    "D-07",
    "D-08",
    "D-09",
    "D-10",
    "D-11",
    "D-12",
    "D-13",
    "D-14",
    "D-15",
    "D-17",
    "D-19",
    "D-20",
)


def test_material_write_applies_all_dsr_checkpoints():
    row = enforce_material_write("signal", dict(_BASE))
    applied = row.get("dsr_checkpoints_applied") or []
    for dsr_id in DSR_PARTIAL_IDS:
        assert dsr_id in applied
    assert row.get("dsr_001_contract_bound")
    assert row.get("dsr_002_contract_complete")
    assert row.get("dsr_024_flywheel_gate") == "closed"


@pytest.mark.parametrize("dsr_id", DSR_PARTIAL_IDS)
def test_dsr_checkpoint_removal_fails(dsr_id: str, monkeypatch):
    from data_governance.dsr_checkpoints import DSR_CHECKPOINTS

    def _boom(_surface, _payload):
        raise RuntimeError(f"{dsr_id}_control_removed")

    monkeypatch.setitem(DSR_CHECKPOINTS, dsr_id, _boom)
    with pytest.raises(RuntimeError, match=f"{dsr_id}_control_removed"):
        enforce_material_write("signal", dict(_BASE))


@pytest.mark.parametrize("defect_id", D_PARTIAL_IDS)
def test_d_defect_maps_to_dsr_checkpoint(defect_id: str):
    from data_governance.dsr_checkpoints import D_TO_DSR, DSR_CHECKPOINTS

    mapped = D_TO_DSR[defect_id]
    assert mapped in DSR_CHECKPOINTS or mapped in {"DSR-005", "DSR-008", "DSR-012", "DSR-016"}


def test_dsr_003_pit_contract_on_backtest():
    row = enforce_material_write("signal", {**_BASE, "purpose": "backtest"})
    assert row.get("pit_contract")
    assert row.get("dsr_003_checked")


def test_dsr_007_correction_requires_bitemporal_fields():
    with pytest.raises(GovernanceViolationError, match="dsr_007"):
        enforce_material_write(
            "signal",
            {**_BASE, "is_correction": True, "correction_of": "row-1"},
        )


def test_dsr_009_outcome_requires_evaluator_version():
    with pytest.raises(GovernanceViolationError, match="dsr_009"):
        enforce_material_write("decision", {**_BASE, "outcome": "win", "decision_id": "d1"})


def test_dsr_011_blocks_conflicted_display():
    with pytest.raises(GovernanceViolationError, match="dsr_011"):
        enforce_material_write(
            "signal",
            {
                **_BASE,
                "entity_id": "wallet-1",
                "entity_assertion": {"conflict_state": "CONFLICTED"},
                "allow_conflicted_display": True,
            },
        )


def test_dsr_017_degrades_low_quality():
    from data_governance.dsr_checkpoints import checkpoint_dsr_017

    row = checkpoint_dsr_017("signal", {**_BASE, "data_quality_score": 30.0})
    assert row.get("availability") == "degraded"
    assert row.get("quality_degradation_applied")
