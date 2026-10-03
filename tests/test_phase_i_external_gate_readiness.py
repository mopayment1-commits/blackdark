"""Phase I external-gate activation readiness tests."""

from __future__ import annotations

import json
from pathlib import Path

from data_governance.phase_i_external_adapters import (
    PHASE_I_EXTERNAL_ROUTE_SPECS,
    build_external_gate_readiness_matrix,
    run_phase_i_external_path,
)
from data_governance.phase_i_runtime import build_phase_i_runtime_reconciliation

COMPLIANCE = Path(__file__).resolve().parents[1] / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"


def test_all_seven_external_routes_fixture_path():
    for source_id in PHASE_I_EXTERNAL_ROUTE_SPECS:
        out = run_phase_i_external_path(source_id)
        assert out.get("data_governance_state")
        assert out.get("todays_decision_surface")
        assert out.get("data_governance", {}).get("provenance")


def test_disposition_arithmetic_sums_to_31():
    recon = build_phase_i_runtime_reconciliation()
    counts = recon["DISPOSITION_COUNTS"]
    assert recon["PHASE_I_SELECTED_SOURCE_ROUTES"] == 31
    assert recon["DISPOSITION_COUNT_SUM"] == 31
    assert recon["DISPOSITION_COUNT_MISMATCH"] == 0
    assert sum(counts.values()) == 31


def test_external_gate_readiness_matrix():
    matrix = build_external_gate_readiness_matrix()
    assert matrix["EXTERNAL_GATED_ROUTES_AUDITED"] == 7
    assert matrix["EXTERNAL_GATED_ROUTES_WITH_LOCAL_ENGINEERING_REMAINING"] == 0
    assert matrix["EXTERNAL_GATED_ROUTES_WITHOUT_ACTIVATION_READINESS"] == 0
    for row in matrix["rows"]:
        assert row["NO_LOCAL_ENGINEERING_REMAINS"] is True
        assert row["READY_TO_ACTIVATE_WITH_EXTERNAL_DEPENDENCY_ONLY"] is True


def test_remediated_external_dispositions():
    recon = build_phase_i_runtime_reconciliation()
    external = [r for r in recon["rows"] if r["source_route"] in PHASE_I_EXTERNAL_ROUTE_SPECS]
    assert len(external) == 7
    assert all(r["final_disposition"] == "LOCAL_GAP_REMEDIATED_THEN_EXTERNAL_GATED" for r in external)
