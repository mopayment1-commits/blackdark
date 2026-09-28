#!/usr/bin/env python3
"""Dependency-based regression impact matrix for Data Governance changes (§33)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"

CHANGED_MODULES = [
    {
        "module": "data_governance/pipeline.py",
        "direct_dependents": ["decision_enrichment.py", "api/routers/data_governance.py"],
        "indirect_dependents": ["decision_truth/admission.py", "dashboard.py"],
        "canonical_systems": ["Decision Truth", "Data Truth Fabric"],
        "tests": [
            "tests/test_data_governance_p0_test_matrix.py",
            "tests/test_data_gov_closure.py",
            "tests/test_data_gov_fault_injection.py",
        ],
    },
    {
        "module": "data_governance/reconciliation.py",
        "direct_dependents": ["data_governance/pipeline.py"],
        "indirect_dependents": ["decision_enrichment.py", "decision_truth/admission.py"],
        "canonical_systems": ["Cross-source reconciliation", "Decision Truth"],
        "tests": ["tests/test_data_governance_reconciliation.py"],
    },
    {
        "module": "data_governance/phase_i.py",
        "direct_dependents": ["data_governance/restore.py", "scripts/data_gov_gate_runner.py"],
        "indirect_dependents": [],
        "canonical_systems": ["Source registry", "Phase gate"],
        "tests": ["tests/test_data_gov_closure.py"],
    },
    {
        "module": "decision_enrichment.py",
        "direct_dependents": ["dashboard.py"],
        "indirect_dependents": ["decision_truth/pipeline.py"],
        "canonical_systems": ["Adaptive Intelligence", "Decision Truth"],
        "tests": ["tests/test_data_governance_p0_test_matrix.py"],
        "adaptive_v4_note": "Wiring extension only; does not reopen Adaptive v4 baseline SHA 07bb4049",
    },
]


def _run_tests() -> dict[str, str]:
    results = {}
    for entry in CHANGED_MODULES:
        for test in entry["tests"]:
            if test in results:
                continue
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", test, "-q", "--tb=no"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            results[test] = "PASS" if proc.returncode == 0 else "FAIL"
    return results


def main() -> int:
    test_results = _run_tests()
    uncovered = []
    for entry in CHANGED_MODULES:
        for test in entry["tests"]:
            if test_results.get(test) != "PASS":
                uncovered.append(f"{entry['module']}:{test}")

    payload = {
        "AFFECTED_MODULES_WITHOUT_REGRESSION_COVERAGE": len(uncovered),
        "uncovered": uncovered,
        "adaptive_v4_baseline_reopen_required": False,
        "adaptive_v4_baseline_sha": "07bb4049",
        "adaptive_v4_integrity_note": "Data governance adds admission gate wiring; no canonical Adaptive v4 contract change",
        "test_results": test_results,
        "modules": CHANGED_MODULES,
    }
    (OUT_DIR / "DATA_GOV_REGRESSION_IMPACT_MATRIX.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k not in ("modules",)}, indent=2))
    return 0 if not uncovered else 1


if __name__ == "__main__":
    raise SystemExit(main())
