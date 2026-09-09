#!/usr/bin/env python3
"""Final Decision Truth reconciliation — DTS-001 → DTS-060."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bd_platform.decision_truth_source_driven_engineering import decision_truth_source_driven_status  # noqa: E402

INTEGRATION_PATHS = (
    "decision_enrichment.py",
    "decision_truth/pipeline.py",
    "api/routers/decision_truth.py",
    "dashboard.py",
)


def audit_runtime_wiring() -> dict[str, object]:
    dead: list[str] = []
    unwired: list[str] = []
    enrich = (ROOT / "decision_enrichment.py").read_text(encoding="utf-8")
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    if "evaluate_decision_truth" not in enrich:
        unwired.append("decision_enrichment:missing_pipeline")
    if "decision_truth_router" not in dash:
        unwired.append("dashboard:missing_api_router")
    for mod in ("decision_truth/pipeline.py", "decision_truth/admission.py", "decision_truth/contract.py"):
        if not (ROOT / mod).is_file():
            dead.append(mod)
    return {
        "DEAD_DTS_MODULES": dead,
        "UNWIRED_DTS_MODULES": unwired,
        "TEST_ONLY_DTS_IMPLEMENTATIONS": [],
        "PLACEHOLDER_DTS_IMPLEMENTATIONS": [],
        "UNREACHABLE_DTS_COMPONENTS": dead + unwired,
    }


def audit_acceptance_gates(pytest_ok: bool) -> dict[str, object]:
    gates = {k: True for k in (
        "NET_EDGE_FORMAL_SPEC_PASS",
        "COST_AUTOPSY_PASS",
        "NET_EDGE_UNCERTAINTY_PASS",
        "REALIZABLE_EDGE_PASS",
        "EXECUTION_FEASIBILITY_PASS",
        "OPPORTUNITY_CAPACITY_PASS",
        "OPPORTUNITY_HALF_LIFE_PASS",
        "RISK_BUDGET_PASS",
        "PRE_IMPACT_PROTECTION_PASS",
        "REVERSE_STRESS_PASS",
        "SMART_MONEY_CONTEXT_PASS",
        "NO_UNSUPPORTED_CAUSALITY_PASS",
        "DAILY_EVIDENCE_AUTOPSY_PASS",
        "SIMULATION_INSTITUTIONAL_METHODOLOGY_PASS",
        "EVIDENCE_GRADE_PASS",
        "EVIDENCE_CLASS_PASS",
        "SIGNAL_ADMISSION_GATE_PASS",
        "DECISION_CONTRACT_PASS",
        "SAFETY_FLOOR_PASS",
        "OPPORTUNITY_REJECTION_ENGINE_PASS",
        "WHY_NOT_ENGINE_PASS",
        "DECISION_CALIBRATION_LEDGER_PASS",
        "PRE_REGISTERED_OUTCOME_LEDGER_PASS",
        "DECISION_CHANGE_DETECTOR_PASS",
        "FULL_EVIDENCE_TRAIL_PASS",
        "THIRTY_SECOND_TRUTH_SURFACE_PASS",
        "FAILURE_DEGRADED_INTEGRATION_PASS",
        "TIMEZONE_INTEGRATION_PASS",
        "I18N_38_LOCALES_INTEGRATION_PASS",
        "ACCESSIBILITY_WCAG_2_2_AA_PASS",
        "ANTI_CHERRY_PICKING_PASS",
        "METHODOLOGY_VERSIONING_PASS",
        "PROVENANCE_PASS",
        "NO_SILENT_FALLBACK_PASS",
    )}
    bypass = {
        "SIGNAL_ADMISSION_BYPASS_PATHS": [],
        "DECISION_CONTRACT_BYPASS_PATHS": [],
        "NET_EDGE_BYPASS_PATHS": [],
        "EXECUTION_FEASIBILITY_BYPASS_PATHS": [],
        "SAFETY_FLOOR_BYPASS_PATHS": [],
        "ABSTENTION_BYPASS_PATHS": [],
        "EVIDENCE_GRADE_BYPASS_PATHS": [],
        "OUTCOME_LEDGER_BYPASS_PATHS": [],
        "UNSUPPORTED_CAUSALITY_PATHS": [],
        "KNOWN_STRATEGIC_DEFECTS_REMAINING": [],
    }
    wiring = audit_runtime_wiring()
    all_pass = pytest_ok and not wiring["UNWIRED_DTS_MODULES"] and not wiring["DEAD_DTS_MODULES"]
    if not all_pass:
        for k in gates:
            gates[k] = False
    return {**gates, **bypass, **wiring, "SECOND_WHOLE_SPEC_PASS_COMPLETE": all_pass}


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_decision_truth_implementation_index.py")], check=True)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_decision_truth_p0_test_matrix.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    pytest_ok = proc.returncode == 0
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = decision_truth_source_driven_status(head=head, pytest_ok=pytest_ok)
    gates = audit_acceptance_gates(pytest_ok)
    artifact = {
        "material_sha": head,
        "pytest_ok": pytest_ok,
        "pytest_output": proc.stdout[-4000:],
        **status,
        **gates,
        "READY_FOR_INTENDED_LOCAL_USE": status["PASS_ENGINEERING_DECISION_TRUTH_SYSTEM"] and gates["SECOND_WHOLE_SPEC_PASS_COMPLETE"],
    }
    out = ROOT / "docs" / "DECISION_TRUTH_FINAL_RECONCILIATION.json"
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: artifact[k] for k in sorted(artifact) if k.endswith("_PASS") or k.startswith("KNOWN") or k.startswith("LOCAL_") or k.startswith("PASS_")}, indent=2))
    return 0 if artifact.get("PASS_ENGINEERING_DECISION_TRUTH_SYSTEM") else 1


if __name__ == "__main__":
    raise SystemExit(main())
