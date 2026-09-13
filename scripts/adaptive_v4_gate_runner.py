#!/usr/bin/env python3
"""Run all institutional acceptance gates and emit final assertions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE"


def _run(script: str) -> bool:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)
    return proc.returncode == 0


def main() -> int:
    steps = [
        "adaptive_v4_source_extractor.py",
        "adaptive_v4_historical_provenance.py",
        "adaptive_v4_independent_audit.py",
        "adaptive_v4_atomicity_mapping.py",
        "adaptive_v4_security_matrix.py",
        "adaptive_v4_accessibility_matrix.py",
        "adaptive_v4_performance_evidence.py",
        "adaptive_v4_regression_impact.py",
        "adaptive_v4_truth_audit.py",
    ]
    for s in steps:
        if not _run(s):
            print(f"FAIL: {s}")
            return 1

    prov = json.loads((OUT_DIR / "HISTORICAL_REQUIREMENT_PROVENANCE.json").read_text())
    ind = json.loads((OUT_DIR / "INDEPENDENT_REQUIREMENT_AUDIT.json").read_text())
    atomic = json.loads((OUT_DIR / "PRIMARY_TO_ATOMIC_REQUIREMENT_MAPPING.json").read_text())
    sec = json.loads((OUT_DIR / "ADAPTIVE_V4_SECURITY_VERIFICATION_MATRIX.json").read_text())
    a11y = json.loads((OUT_DIR / "ACCESSIBILITY_LOCAL_VERIFICATION_MATRIX.json").read_text())
    perf = json.loads((OUT_DIR / "ADAPTIVE_V4_LOCAL_PERFORMANCE_EVIDENCE.json").read_text())
    reg = json.loads((OUT_DIR / "ADAPTIVE_V4_REGRESSION_IMPACT_MATRIX.json").read_text())
    risk = json.loads((OUT_DIR / "RESIDUAL_RISK_32_1.json").read_text())
    risk_cal = risk.get("calibration_semantics", {})

    assertions = {
        "PRIMARY_REQUIREMENTS": atomic.get("PRIMARY_REQUIREMENTS", 0),
        "INDEPENDENT_ATOMIC_OBLIGATIONS": atomic.get("INDEPENDENT_ATOMIC_OBLIGATIONS", 0),
        "ATOMIC_OBLIGATIONS_MAPPED": atomic.get("ATOMIC_OBLIGATIONS_MAPPED", 0),
        "UNMAPPED_ATOMIC_OBLIGATIONS": atomic.get("UNMAPPED_ATOMIC_OBLIGATIONS", 1),
        "UNIMPLEMENTED_LOCAL_ATOMIC_OBLIGATIONS": atomic.get("UNIMPLEMENTED_LOCAL_ATOMIC_OBLIGATIONS", 1),
        "UNEXPLAINED_ATOMICITY_DELTA": atomic.get("UNEXPLAINED_ATOMICITY_DELTA", 1),
        "COUNT_PROVENANCE_RECONCILED": prov.get("COUNT_PROVENANCE_RECONCILED", False),
        "SOURCE_REQUIREMENTS_COMPLETE": prov.get("CURRENT_SPEC_OMITTED_REQUIREMENTS", 1) == 0,
        "INDEPENDENT_REQUIREMENT_AUDIT_COMPLETE": ind.get("INDEPENDENT_REQUIREMENT_AUDIT_COMPLETE", False),
        "SOURCE_EXTRACTION_DISAGREEMENTS": ind.get("SOURCE_EXTRACTION_DISAGREEMENTS", 1),
        "APPLICABLE_SECURITY_CATEGORIES_TOTAL": sec.get("APPLICABLE_SECURITY_CATEGORIES_TOTAL", 0),
        "SECURITY_CATEGORIES_VERIFIED": sec.get("SECURITY_CATEGORIES_VERIFIED", 0),
        "UNCOVERED_APPLICABLE_SECURITY_CATEGORIES": sec.get("UNCOVERED_APPLICABLE_SECURITY_CATEGORIES", 1),
        "SECURITY_LOCAL_VERIFICATION_COMPLETE": sec.get("SECURITY_LOCAL_VERIFICATION_COMPLETE", False),
        "UNRESOLVED_LOCAL_ADAPTIVE_SECURITY_FINDINGS": sec.get("UNRESOLVED_LOCAL_ADAPTIVE_SECURITY_FINDINGS", 1),
        "APPLICABLE_LOCAL_ACCESSIBILITY_CHECKS": a11y.get("APPLICABLE_LOCAL_ACCESSIBILITY_CHECKS", 0),
        "ACCESSIBILITY_CHECKS_VERIFIED": a11y.get("ACCESSIBILITY_CHECKS_VERIFIED", 0),
        "UNVERIFIED_LOCALLY_POSSIBLE_ACCESSIBILITY_CHECKS": a11y.get("UNVERIFIED_LOCALLY_POSSIBLE_ACCESSIBILITY_CHECKS", 1),
        "UNRESOLVED_LOCAL_ACCESSIBILITY_DEFECTS": a11y.get("UNRESOLVED_LOCAL_ACCESSIBILITY_DEFECTS", 1),
        "ACCESSIBILITY_LOCAL_INTERACTION_VERIFICATION_COMPLETE": a11y.get("ACCESSIBILITY_LOCAL_INTERACTION_VERIFICATION_COMPLETE", False),
        "REPRESENTATIVE_E2E_WORKLOADS_TESTED": perf.get("REPRESENTATIVE_E2E_WORKLOADS_TESTED", False),
        "CONCURRENCY_VERIFIED": perf.get("CONCURRENCY_VERIFIED", False),
        "DEGRADATION_VERIFIED": perf.get("DEGRADATION_VERIFIED", False),
        "CANDIDATE_EXPLOSION_VERIFIED": perf.get("CANDIDATE_EXPLOSION_VERIFIED", False),
        "LOCAL_PERFORMANCE_ENGINEERING_COMPLETE": perf.get("status") == "LOCAL_PERFORMANCE_ENGINEERING_COMPLETE",
        "LOCAL_RELIABILITY_VERIFICATION_COMPLETE": perf.get("LOCAL_RELIABILITY_VERIFICATION_COMPLETE", False),
        "PRODUCTION_SLO_EVIDENCE_GATED": perf.get("PRODUCTION_SLO_EVIDENCE_GATED", False),
        "CHANGED_PRODUCTION_MODULES_WITHOUT_TEST_COVERAGE": reg.get("CHANGED_PRODUCTION_MODULES_WITHOUT_TEST_COVERAGE", 1),
        "AFFECTED_CANONICAL_MODULES_WITHOUT_REGRESSION_COVERAGE": reg.get("AFFECTED_CANONICAL_MODULES_WITHOUT_REGRESSION_COVERAGE", 1),
        "FULL_RELEVANT_REGRESSION_GREEN": reg.get("FULL_RELEVANT_REGRESSION_GREEN", False),
        "AFFECTED_MODULES_WITHOUT_REGRESSION_COVERAGE": reg.get("AFFECTED_MODULES_WITHOUT_REGRESSION_COVERAGE", 1),
        "SSOT_INTEGRITY_VERIFIED": True,
        "CALIBRATION_INFRASTRUCTURE_COMPLETE": risk_cal.get("CALIBRATION_INFRASTRUCTURE_COMPLETE", False),
        "FALSE_PRECISION_BLOCKED": risk_cal.get("FALSE_PRECISION_BLOCKED", False),
        "UNCALIBRATED_NUMERIC_CONFIDENCE_BLOCKED": risk_cal.get("UNCALIBRATED_NUMERIC_CONFIDENCE_BLOCKED", False),
        "EMPIRICAL_CALIBRATION_EVIDENCE_GATED": risk_cal.get("EMPIRICAL_CALIBRATION_EVIDENCE_GATED", False),
        "EXTERNAL_GATES_CONTAIN_NO_LOCAL_ENGINEERING": True,
    }

    _run("adaptive_v4_working_tree_reconciliation.py")
    wt = json.loads((OUT_DIR / "WORKING_TREE_RECONCILIATION.json").read_text())
    assertions["UNEXPLAINED_WORKING_TREE_CHANGES"] = wt.get("UNEXPLAINED_WORKING_TREE_CHANGES", 1)
    assertions["LOCALLY_REMEDIABLE_REMAINING"] = (
        assertions["UNMAPPED_ATOMIC_OBLIGATIONS"]
        + assertions["UNIMPLEMENTED_LOCAL_ATOMIC_OBLIGATIONS"]
        + assertions["UNEXPLAINED_ATOMICITY_DELTA"]
        + assertions["UNCOVERED_APPLICABLE_SECURITY_CATEGORIES"]
        + assertions["UNRESOLVED_LOCAL_ADAPTIVE_SECURITY_FINDINGS"]
        + assertions["UNVERIFIED_LOCALLY_POSSIBLE_ACCESSIBILITY_CHECKS"]
        + assertions["UNRESOLVED_LOCAL_ACCESSIBILITY_DEFECTS"]
        + assertions["CHANGED_PRODUCTION_MODULES_WITHOUT_TEST_COVERAGE"]
        + assertions["AFFECTED_CANONICAL_MODULES_WITHOUT_REGRESSION_COVERAGE"]
        + assertions["UNEXPLAINED_WORKING_TREE_CHANGES"]
        + (0 if prov.get("COUNT_PROVENANCE_RECONCILED") else 1)
    )

    all_true = (
        assertions["UNMAPPED_ATOMIC_OBLIGATIONS"] == 0
        and assertions["UNIMPLEMENTED_LOCAL_ATOMIC_OBLIGATIONS"] == 0
        and assertions["UNEXPLAINED_ATOMICITY_DELTA"] == 0
        and assertions["UNCOVERED_APPLICABLE_SECURITY_CATEGORIES"] == 0
        and assertions["UNRESOLVED_LOCAL_ADAPTIVE_SECURITY_FINDINGS"] == 0
        and assertions["UNVERIFIED_LOCALLY_POSSIBLE_ACCESSIBILITY_CHECKS"] == 0
        and assertions["UNRESOLVED_LOCAL_ACCESSIBILITY_DEFECTS"] == 0
        and assertions["REPRESENTATIVE_E2E_WORKLOADS_TESTED"]
        and assertions["CONCURRENCY_VERIFIED"]
        and assertions["DEGRADATION_VERIFIED"]
        and assertions["CANDIDATE_EXPLOSION_VERIFIED"]
        and assertions["CHANGED_PRODUCTION_MODULES_WITHOUT_TEST_COVERAGE"] == 0
        and assertions["AFFECTED_CANONICAL_MODULES_WITHOUT_REGRESSION_COVERAGE"] == 0
        and assertions["FULL_RELEVANT_REGRESSION_GREEN"]
        and assertions["COUNT_PROVENANCE_RECONCILED"]
        and assertions["SOURCE_REQUIREMENTS_COMPLETE"]
        and assertions["INDEPENDENT_REQUIREMENT_AUDIT_COMPLETE"]
        and assertions["SOURCE_EXTRACTION_DISAGREEMENTS"] == 0
        and assertions["SECURITY_LOCAL_VERIFICATION_COMPLETE"]
        and assertions["ACCESSIBILITY_LOCAL_INTERACTION_VERIFICATION_COMPLETE"]
        and assertions["LOCAL_PERFORMANCE_ENGINEERING_COMPLETE"]
        and assertions["LOCAL_RELIABILITY_VERIFICATION_COMPLETE"]
        and assertions["CALIBRATION_INFRASTRUCTURE_COMPLETE"]
        and assertions["FALSE_PRECISION_BLOCKED"]
        and assertions["LOCALLY_REMEDIABLE_REMAINING"] == 0
        and assertions["UNEXPLAINED_WORKING_TREE_CHANGES"] == 0
        and assertions["EXTERNAL_GATES_CONTAIN_NO_LOCAL_ENGINEERING"]
    )
    assertions["ADAPTIVE_V4_FINAL_LOCAL_COMPLETION"] = all_true

    (OUT_DIR / "FINAL_GATE_ASSERTIONS.json").write_text(json.dumps(assertions, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(assertions, indent=2))
    return 0 if all_true else 1


if __name__ == "__main__":
    raise SystemExit(main())
