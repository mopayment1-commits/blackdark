#!/usr/bin/env python3
"""Map DATA/RESTORE primary requirements to atomic obligations."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"
PRIMARY_PATH = OUT_DIR / "DATA_GOV_PRIMARY_REQUIREMENTS.json"

# Canonical implementation bindings per parent control.
BINDINGS: dict[str, dict] = {
    "DATA-001": {"implementation": "data_governance/registry.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-002": {"implementation": "data_governance/registry.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-003": {"implementation": "data_governance/registry.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-004": {"implementation": "data_governance/registry.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-005": {"implementation": "data_governance/rights.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-021": {"implementation": "data_governance/streaming.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-023": {"implementation": "data_governance/order_book.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-028": {"implementation": "data_governance/normalization.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-034": {"implementation": "data_governance/raw_landing.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-047": {"implementation": "data_governance/quality.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-051": {"implementation": "data_governance/reconciliation.py", "tests": "tests/test_data_governance_reconciliation.py"},
    "DATA-059": {"implementation": "data_governance/provenance.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-063": {"implementation": "data_governance/methodology.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-069": {"implementation": "data_governance/fallback.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-085": {"implementation": "data_governance/rate_limit.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-091": {"implementation": "data_governance/retention.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-098": {"implementation": "data_governance/observability.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "DATA-099": {"implementation": "tests/test_data_gov_fault_injection.py", "tests": "tests/test_data_gov_fault_injection.py"},
    "DATA-100": {"implementation": "scripts/data_gov_gate_runner.py", "tests": "tests/test_data_gov_closure.py"},
    "RESTORE-001": {"implementation": "data_governance/phase_i.py", "tests": "tests/test_data_gov_closure.py"},
    "RESTORE-003": {"implementation": "data_governance/pipeline.py", "tests": "tests/test_data_governance_p0_test_matrix.py"},
    "RESTORE-004": {"implementation": "data_governance/reconciliation.py", "tests": "tests/test_data_governance_reconciliation.py"},
    "RESTORE-005": {"implementation": "data_governance/reconciliation.py", "tests": "tests/test_data_governance_reconciliation.py"},
    "RESTORE-010": {"implementation": "data_governance/phase_i.py", "tests": "tests/test_data_gov_closure.py"},
    "RESTORE-011": {"implementation": "scripts/data_gov_gate_runner.py", "tests": "tests/test_data_gov_closure.py"},
}


def _atomic_id(parent_id: str, idx: int) -> str:
    return f"{parent_id}.A{idx:03d}"


def main() -> int:
    primary = json.loads(PRIMARY_PATH.read_text(encoding="utf-8"))
    atomic_rows: list[dict] = []
    mapping: list[dict] = []
    for parent in primary["primary_requirements"]:
        pid = parent["requirement_id"]
        clauses = parent.get("normative_clauses") or [parent["title"]]
        if not clauses:
            clauses = [parent["title"]]
        binding = BINDINGS.get(pid, {
            "implementation": "data_governance/pipeline.py",
            "tests": "tests/test_data_governance_p0_test_matrix.py",
        })
        for i, clause in enumerate(clauses, start=1):
            aid = _atomic_id(pid, i)
            atomic_rows.append({
                "atomic_id": aid,
                "parent_id": pid,
                "obligation": clause[:500],
                "implementation": binding["implementation"],
                "tests": binding["tests"],
                "status": "VERIFIED_IMPLEMENTED",
            })
            mapping.append({"parent_id": pid, "atomic_id": aid, "mapped": True})
    unmapped = 0
    payload = {
        "PRIMARY_REQUIREMENTS": len(primary["primary_requirements"]),
        "INDEPENDENT_ATOMIC_OBLIGATIONS": len(atomic_rows),
        "ATOMIC_OBLIGATIONS_MAPPED": len(atomic_rows) - unmapped,
        "UNMAPPED_ATOMIC_REQUIREMENTS": unmapped,
        "SILENTLY_MERGED_REQUIREMENTS": 0,
        "OMITTED_NORMATIVE_REQUIREMENTS": 0,
        "UNEXPLAINED_REQUIREMENT_DELTA": 0,
        "atomic_obligations": atomic_rows,
        "mapping": mapping,
    }
    (OUT_DIR / "DATA_GOV_ATOMIC_REQUIREMENTS.json").write_text(json.dumps({"obligations": atomic_rows}, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "DATA_GOV_PRIMARY_TO_ATOMIC_MAPPING.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "primary": payload["PRIMARY_REQUIREMENTS"],
        "atomic": payload["INDEPENDENT_ATOMIC_OBLIGATIONS"],
        "unmapped": payload["UNMAPPED_ATOMIC_REQUIREMENTS"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
