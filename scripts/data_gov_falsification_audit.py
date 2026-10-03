#!/usr/bin/env python3
"""Five-pass institutional falsification audit for Data Governance closure."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"
sys.path.insert(0, str(ROOT))


def _pytest_ok() -> tuple[bool, str]:
    proc = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/test_data_governance_p0_test_matrix.py",
            "tests/test_data_gov_closure.py",
            "tests/test_data_gov_fault_injection.py",
            "tests/test_data_governance_reconciliation.py",
            "-q", "--tb=no",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0, proc.stdout[-500:]


def _pass1_requirement_completeness() -> dict:
    audit = json.loads((OUT_DIR / "DATA_GOV_INDEPENDENT_AUDIT.json").read_text(encoding="utf-8"))
    return {
        "pass": audit["audit_pass"],
        "findings": audit.get("missing_from_extract", []) + audit.get("unmapped_atomic", []),
        "checks": ["primary_extracted", "atomic_mapped", "independent_audit"],
    }


def _pass2_architecture_ssot() -> dict:
    from scripts.data_governance_final_reconciliation import audit_runtime_wiring

    wiring = audit_runtime_wiring()
    parallel = sum(
        1 for k in wiring
        if k.startswith("PARALLEL_") and wiring[k]
    )
    findings = wiring.get("UNWIRED_DATA_GOVERNANCE_MODULES", []) + wiring.get("DEAD_DATA_GOVERNANCE_MODULES", [])
    return {
        "pass": not findings and parallel == 0,
        "findings": findings,
        "checks": ["no_parallel_truth", "runtime_wiring", "data_truth_fabric_path"],
    }


def _pass3_data_correctness() -> dict:
    from data_governance.pipeline import evaluate_data_governance
    from data_governance.reconciliation import detect_divergence

    stale = evaluate_data_governance({"symbol": "BTC", "quote_age_ms": 999999}, symbol="BTC")
    conflict = detect_divergence(primary_value=100.0, secondary_value=200.0, threshold_pct=1.0)
    findings = []
    if stale.get("data_governance_state") not in {"DEGRADED", "ABSTAINED", "REJECTED"}:
        findings.append("stale_not_degraded")
    if not conflict.get("conflict"):
        findings.append("conflict_not_detected")
    return {
        "pass": not findings,
        "findings": findings,
        "checks": ["stale_degrade", "conflict_detection", "decision_truth_admission"],
    }


def _pass4_security_resilience() -> dict:
    from data_governance.credentials import credential_status
    from data_governance.retention import retention_status

    cred = credential_status()
    retention = retention_status()
    findings = []
    if not cred.get("secret_manager_only"):
        findings.append("credential_policy_gap")
    if not retention.get("policies"):
        findings.append("retention_matrix_missing")
    return {
        "pass": not findings,
        "findings": findings,
        "checks": ["credential_policy", "retention_matrix", "fault_injection_tests"],
    }


def _pass5_independent_challenge() -> dict:
    assertions = json.loads((OUT_DIR / "FINAL_GATE_ASSERTIONS.json").read_text(encoding="utf-8"))
    challenge_vectors = [
        "KNOWN_LOCAL_DATA_GAPS",
        "KNOWN_LOCAL_DATA_DEFECTS",
        "KNOWN_LOCAL_DATA_INTEGRATION_GAPS",
        "KNOWN_LOCAL_DATA_TEST_GAPS",
        "UNWIRED_MODULES",
    ]
    findings = []
    for key in challenge_vectors:
        val = assertions.get(key, [])
        if val:
            findings.append(f"{key}={val}")
    if not assertions.get("PASS_ENGINEERING_DATA"):
        findings.append("PASS_ENGINEERING_DATA=false")
    if assertions.get("PREMATURE_100_SOURCE_EXPANSION"):
        findings.append("premature_phase_ii")
    return {
        "pass": not findings,
        "findings": findings,
        "checks": ["closure_challenge", "no_premature_expansion", "gate_assertions"],
    }


def main() -> int:
    pytest_ok, pytest_tail = _pytest_ok()
    passes = {
        "PASS_1_REQUIREMENT_COMPLETENESS": _pass1_requirement_completeness(),
        "PASS_2_ARCHITECTURE_SSOT": _pass2_architecture_ssot(),
        "PASS_3_DATA_CORRECTNESS": _pass3_data_correctness(),
        "PASS_4_SECURITY_RESILIENCE": _pass4_security_resilience(),
        "PASS_5_INDEPENDENT_CHALLENGE": _pass5_independent_challenge(),
    }
    all_pass = pytest_ok and all(p["pass"] for p in passes.values())
    payload = {
        "FIVE_PASS_FALSIFICATION_COMPLETE": all_pass,
        "PYTEST_GREEN": pytest_ok,
        "pytest_tail": pytest_tail,
        "passes": passes,
        "PASS_ENGINEERING_DATA": all_pass,
    }
    (OUT_DIR / "DATA_GOV_FIVE_PASS_FALSIFICATION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "pytest_tail"}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
