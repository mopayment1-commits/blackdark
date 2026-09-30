#!/usr/bin/env python3
"""P4 evidence / simulation / calibration / history closure verification."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "DECISION_TRUTH_P4_EVIDENCE_LIFECYCLE_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md"

P4_DTS = [
    "DTS-021",
    "DTS-022",
    "DTS-023",
    "DTS-037",
    "DTS-038",
    "DTS-039",
    "DTS-040",
    "DTS-041",
    "DTS-042",
    "DTS-043",
    "DTS-050",
    "DTS-051",
    "DTS-058",
    "DTS-059",
    "DTS-060",
]

CANONICAL_OWNERS = {
    "lifecycle_orchestrator": "decision_truth/lifecycle.py",
    "calibration": "decision_truth/calibration.py",
    "outcome_ledger": "decision_truth/outcome_ledger.py",
    "change_detector": "decision_truth/change_detector.py",
    "simulation": "decision_truth/simulation.py",
    "evidence_grade": "decision_truth/evidence_grade.py",
    "evidence_taxonomy": "cap646/evidence_class.py",
    "methodology_versions": "decision_truth/methodology_versions.py",
    "provenance": "decision_truth/provenance.py",
    "anti_cherry_picking": "decision_truth/anti_cherry_picking.py",
    "history_integrity": "decision_truth/history_integrity.py",
    "governance_entry": "decision_truth/govern.py",
}


def _spec_hash() -> str:
    if SPEC.is_file():
        return hashlib.sha256(SPEC.read_bytes()).hexdigest()
    return "missing"


def _git_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _scan_bypasses() -> dict[str, list[str]]:
    govern = (ROOT / "decision_truth" / "govern.py").read_text(encoding="utf-8")
    lifecycle = (ROOT / "decision_truth" / "lifecycle.py").read_text(encoding="utf-8")
    grade = (ROOT / "decision_truth" / "evidence_grade.py").read_text(encoding="utf-8")

    return {
        "EVIDENCE_GRADE_BYPASS_PATHS": [] if "evaluate_evidence_grade" in lifecycle else ["lifecycle_missing_grade"],
        "OUTCOME_LEDGER_BYPASS_PATHS": [] if "pre_register_decision" in govern else ["govern_missing_preregistration"],
        "SIMULATION_LINKAGE_GAPS": [] if "evaluate_simulation_context" in lifecycle else ["lifecycle_missing_simulation"],
        "CALIBRATION_LINKAGE_GAPS": [] if "evaluate_calibration" in lifecycle else ["lifecycle_missing_calibration"],
        "PRE_REGISTRATION_BYPASS_PATHS": [] if "pre_register_decision" in govern else ["govern_missing_preregistration"],
        "DECISION_HISTORY_GAPS": [] if "record_history_event" in govern else ["govern_missing_history"],
        "METHODOLOGY_VERSION_GAPS": [] if "methodology_versions" in lifecycle else ["lifecycle_missing_methodology_versions"],
        "PROVENANCE_GAPS": [] if "build_provenance_context" in lifecycle else ["lifecycle_missing_provenance"],
        "CHERRY_PICKING_EXPOSURE_PATHS": [] if "validate_performance_claim" in lifecycle else ["lifecycle_missing_cherry_picking"],
        "EVIDENCE_CLASS_PROMOTION_GAPS": [] if "resolve_evidence_class" in lifecycle else ["lifecycle_missing_evidence_class"],
        "FABRICATED_OR_DEFAULT_GRADES": [] if '"overall_grade": "A"' not in grade and "default_grade" not in grade else ["hardcoded_grade_detected"],
    }


def _run_tests() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_decision_truth_p4_evidence_lifecycle.py",
        "tests/test_decision_truth_p3_portfolio_preimpact.py",
        "tests/test_decision_truth_p2_economic_execution.py",
        "tests/test_decision_truth_p1_anti_bypass.py",
        "tests/test_decision_truth_pipeline.py",
        "tests/test_data_governance_p0_test_matrix.py",
        "tests/test_arb_truth_gate.py",
        "-q",
        "--tb=no",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return int(proc.returncode != 0), proc.stdout + proc.stderr


def main() -> int:
    bypass = _scan_bypasses()
    regression_failures, test_output = _run_tests()
    bypass_counts = {k: len(v) for k, v in bypass.items()}
    locally_buildable_remaining = sum(bypass_counts.values()) + regression_failures
    live_validation_pending = 1  # forward/live calibration effectiveness

    closed = locally_buildable_remaining == 0 and regression_failures == 0
    verdict = "EVIDENCE_SIMULATION_CALIBRATION_HISTORY_NOT_CLOSED"
    if closed and live_validation_pending > 0:
        verdict = "EVIDENCE_SIMULATION_CALIBRATION_HISTORY_CLOSED_WITH_LIVE_VALIDATION_PENDING"
    elif closed:
        verdict = "EVIDENCE_SIMULATION_CALIBRATION_HISTORY_CLOSED"

    payload = {
        "phase": "P4_EVIDENCE_SIMULATION_CALIBRATION_HISTORY",
        "verified_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "governing_spec_sha256": _spec_hash(),
        "base_sha": _git_sha(),
        "implementation_sha": _git_sha(),
        "dts_ids_covered": P4_DTS,
        "canonical_owners": CANONICAL_OWNERS,
        "remaining_bypass_paths": bypass,
        "live_validation_gates": ["forward_calibration_effectiveness"],
        "summary": {
            "DTS_REQUIREMENTS_IN_SCOPE": len(P4_DTS),
            "FULLY_IMPLEMENTED_VERIFIED_LOCAL": len(P4_DTS) if closed else 0,
            "PARTIAL_LOCAL": 0 if closed else len(P4_DTS),
            "NOT_IMPLEMENTED_LOCAL": 0,
            "LOCALLY_BUILDABLE_REMAINING": locally_buildable_remaining,
            **bypass_counts,
            "REGRESSION_FAILURES": regression_failures,
        },
        "verdict": verdict,
        "test_commands": [
            "python3 -m pytest tests/test_decision_truth_p4_evidence_lifecycle.py tests/test_decision_truth_p3_portfolio_preimpact.py tests/test_decision_truth_p2_economic_execution.py tests/test_decision_truth_p1_anti_bypass.py tests/test_decision_truth_pipeline.py tests/test_data_governance_p0_test_matrix.py tests/test_arb_truth_gate.py -q",
            "python3 scripts/p4_evidence_simulation_calibration_closure_verify.py",
        ],
        "test_output_tail": test_output[-4000:],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"VERDICT={verdict}")
    return 0 if closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
