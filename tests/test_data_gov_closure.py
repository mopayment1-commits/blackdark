"""Data governance institutional closure tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPLIANCE = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"


def test_phase_i_scope_defined():
    from data_governance.phase_i import phase_i_summary

    s = phase_i_summary()
    assert s["PHASE_I_SOURCE_SCOPE_DEFINED"] is True
    assert 25 <= s["phase_i_source_count"] <= 35
    assert s["PREMATURE_100_SOURCE_EXPANSION"] is False


def test_restore_decisions_accounted():
    from data_governance.restore import verify_all_restore

    r = verify_all_restore()
    assert r["ok"] >= 10


def test_primary_requirements_extracted():
    p = COMPLIANCE / "DATA_GOV_PRIMARY_REQUIREMENTS.json"
    assert p.is_file()
    data = json.loads(p.read_text())
    assert data["DATA_PARENT_COUNT"] >= 90
    assert data["RESTORE_PARENT_COUNT"] == 11


def test_atomic_mapping_complete():
    m = COMPLIANCE / "DATA_GOV_PRIMARY_TO_ATOMIC_MAPPING.json"
    assert m.is_file()
    data = json.loads(m.read_text())
    assert data["UNMAPPED_ATOMIC_REQUIREMENTS"] == 0
    assert data["INDEPENDENT_ATOMIC_OBLIGATIONS"] > 0


def test_phase_i_runtime_reconciliation():
    from data_governance.phase_i_runtime import build_phase_i_runtime_reconciliation

    r = build_phase_i_runtime_reconciliation()
    assert r["PHASE_I_SELECTED_SOURCE_ROUTES"] == 31
    assert r["FULLY_ACCOUNTED_PHASE_I_SOURCE_ROUTES"] == 31
    assert r["INCOMPLETE_LOCAL_PHASE_I_SOURCE_ROUTES"] == 0
    assert r["UNEXPLAINED_PHASE_I_ROWS"] == 0
    assert r["PHASE_I_RUNTIME_WIRING_RECONCILED"] is True
    assert len(r["rows"]) == 31


def test_data_truth_fabric_pipeline():
    from data_governance.pipeline import evaluate_data_governance

    out = evaluate_data_governance({"symbol": "ETH", "quote_age_ms": 500}, symbol="ETH")
    assert out.get("raw_evidence_id")
    assert out.get("data_governance")
    assert out.get("todays_decision_surface")
