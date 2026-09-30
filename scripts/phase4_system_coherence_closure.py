#!/usr/bin/env python3
"""Phase 4 — System Coherence + Cross-Spec Integration + E2E Resilience closure."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from phase4_system_coherence_rules import (  # noqa: E402
    GRAPH_PATH,
    SSOT_PATH,
    aggregate_counters,
    build_cross_spec_matrix,
    check_adaptive_anonymous,
    check_contradictions,
    check_data_governance,
    check_decision_traceability,
    check_fds_security,
    check_graph,
    check_shared_cores,
    check_temporal_timezone,
    load_json,
    load_ssot,
    pass_engineering_caps,
    save_json,
    verify_e2e_workflows,
    verify_resilience,
)

MATRIX_PATH = ROOT / "BLACKDARK_CAPABILITY_CROSS_SPEC_TRACEABILITY_MATRIX.json"
EVIDENCE_PATH = ROOT / "BLACKDARK_CAPABILITY_SYSTEM_COHERENCE_EVIDENCE.json"


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def run_pytest_subset() -> dict:
    tests = [
        "tests/test_rc2_chaos_resilience.py",
        "tests/cap646/test_institutional_batch26_strict.py",
        "scripts/phase3_genuinely_independent_verifier.py",
    ]
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=no"] + tests
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
        return {
            "command": " ".join(cmd),
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-1000:] if proc.stderr else "",
            "passed": proc.returncode == 0,
        }
    except Exception as exc:
        return {"command": " ".join(cmd), "passed": False, "error": str(exc)}


def closure_verdict(counters: dict[str, Any]) -> str:
    required_zero = (
        "ORPHAN_CAPABILITIES",
        "BROKEN_GRAPH_EDGES",
        "FALSE_GRAPH_EDGES",
        "MISSING_CRITICAL_EDGES",
        "UNCONTROLLED_CYCLES",
        "CONFLICTING_DEPENDENCY_CHAINS",
        "CONTRADICTORY_CANONICAL_CALCULATIONS",
        "DUPLICATE_TRUTH_IMPLEMENTATIONS",
        "UNRECONCILED_SOURCE_DISAGREEMENTS",
        "PRECISION_OR_ROUNDING_CONFLICTS",
        "UNKNOWN_ZERO_SEMANTIC_ERRORS",
        "TEMPORAL_SEMANTIC_CONFLICTS",
        "TIMEZONE_SEMANTIC_GAPS",
        "DATA_GOVERNANCE_BYPASSES",
        "PARALLEL_STORAGE_TRUTHS",
        "DUPLICATE_LEDGER_PATHS",
        "DECISION_INPUTS_WITHOUT_TRACEABILITY",
        "FALSE_DECISION_CONTRIBUTORS",
        "FDS_BYPASS_PATHS",
        "PARALLEL_SECURITY_IMPLEMENTATIONS",
        "ADAPTIVE_EXPERIENCE_TRUTH_DIVERGENCES",
        "ANONYMOUS_ACCESS_LEAKS",
        "E2E_WORKFLOW_GAPS",
        "SILENT_CORRUPTION_PATHS",
        "FAIL_OPEN_CRITICAL_PATHS",
        "DEGRADED_MODE_FALSE_SUCCESS_PATHS",
        "RECOVERY_FAILURES",
        "IDEMPOTENCY_FAILURES",
        "SHARED_CORE_CONSUMER_REGRESSION_GAPS",
        "SHARED_CORE_SEMANTIC_COLLISIONS",
        "CROSS_SPEC_UNMAPPED_REQUIREMENTS",
        "SPEC_REQUIREMENTS_WITHOUT_RUNTIME_OWNER",
        "CAPABILITIES_WITH_UNRESOLVED_SPEC_REQUIREMENTS",
        "CROSS_SPEC_REQUIREMENT_CONFLICTS",
        "CROSS_SPEC_DUPLICATE_OWNERS",
        "CROSS_SPEC_PARALLEL_IMPLEMENTATIONS",
        "REGRESSION_FAILURES",
    )
    if counters.get("PASS_ENGINEERING", 0) != 932:
        return "CAPABILITY_SYSTEM_COHERENCE_NOT_CLOSED"
    if any(counters.get(k, 1) != 0 for k in required_zero):
        return "CAPABILITY_SYSTEM_COHERENCE_NOT_CLOSED"
    if counters.get("E2E_WORKFLOWS_DEFINED", 0) != counters.get("E2E_WORKFLOWS_VERIFIED", -1):
        return "CAPABILITY_SYSTEM_COHERENCE_NOT_CLOSED"
    if counters.get("RESILIENCE_SCENARIOS_DEFINED", 0) != counters.get("RESILIENCE_SCENARIOS_VERIFIED", -1):
        return "CAPABILITY_SYSTEM_COHERENCE_NOT_CLOSED"
    if counters.get("CROSS_SPEC_REQUIREMENTS_TOTAL", 0) != counters.get("CROSS_SPEC_REQUIREMENTS_ACCOUNTED", -1):
        return "CAPABILITY_SYSTEM_COHERENCE_NOT_CLOSED"
    return "CAPABILITY_SYSTEM_COHERENCE_CLOSED"


def main() -> int:
    ssot = load_ssot()
    graph = load_json(GRAPH_PATH)
    caps = pass_engineering_caps(ssot)
    matrix = build_cross_spec_matrix(caps)

    graph_r = check_graph(graph, caps)
    decision_r = check_decision_traceability(caps)
    fds_r = check_fds_security(caps, graph)
    temporal_r = check_temporal_timezone(caps)
    data_r = check_data_governance(caps)
    adaptive_r = check_adaptive_anonymous(caps)
    contradiction_r = check_contradictions(caps)
    shared_r = check_shared_cores(caps)
    pytest_r = run_pytest_subset()
    regression_failures = 0 if pytest_r.get("passed") else 1

    counters = aggregate_counters(caps, graph, matrix, regression_failures=regression_failures)
    e2e_r = verify_e2e_workflows(caps)
    resilience_r = verify_resilience()
    counters["TESTED_SHA"] = git_sha()
    verdict = closure_verdict(counters)

    matrix_doc = {
        "schema_version": "phase4_cross_spec_traceability_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tested_sha": counters["TESTED_SHA"],
        "derived_artifact_only": True,
        "not_parallel_ssot": True,
        "spec_sources": list(matrix.get("requirements", [{}])[0].get("source_spec", "") for _ in [0]) or [],
        "summary": matrix["summary"],
        "requirements": matrix["requirements"],
    }
    matrix_doc["spec_sources"] = sorted({r["source_spec"] for r in matrix["requirements"]})
    save_json(MATRIX_PATH, matrix_doc)

    evidence = {
        "schema_version": "phase4_system_coherence_evidence_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tested_sha": counters["TESTED_SHA"],
        "phase3_baseline_sealed": True,
        "phase3_verified_tested_sha": "51efcbbda23c42e8d140562f7ee9c04da21a89f6",
        "governing_standard": "BLACKDARK_CAPABILITY_ENGINEERING_ARCHITECTURE_LIVE_GOVERNING_STANDARD_2026_FINAL.md",
        "prior_closures_preserved": [
            "PHASE2_INDEPENDENT_ENGINEERING_CLOSURE_VERIFIED",
            "PHASE3_REMEDIATION_INTEGRITY_VERIFIED",
            "PHASE3_INDEPENDENT_HERO_PROJECT_INTEGRATION_VERIFIED",
            "PHASE3_FINAL_BASELINE_SEALED",
        ],
        "verdict": verdict,
        "counters": counters,
        "workflows": e2e_r["workflows"],
        "resilience_scenarios": resilience_r["scenarios"],
        "graph_checks": graph_r,
        "decision_traceability": decision_r,
        "fds_security": fds_r,
        "temporal_timezone": temporal_r,
        "data_governance": data_r,
        "adaptive_anonymous": adaptive_r,
        "contradictions": contradiction_r,
        "shared_cores": shared_r,
        "pytest_regression": pytest_r,
        "cross_spec_matrix_path": str(MATRIX_PATH.relative_to(ROOT)),
        "evidence_not_self_derived": True,
    }
    ind_proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "phase4_system_coherence_independent_verifier.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    try:
        evidence["independent_verification"] = json.loads(ind_proc.stdout)
    except json.JSONDecodeError:
        evidence["independent_verification"] = {
            "verdict": "PHASE4_INDEPENDENT_VERIFICATION_FAILED",
            "stdout": ind_proc.stdout[-2000:],
            "stderr": ind_proc.stderr[-1000:],
        }
    save_json(EVIDENCE_PATH, evidence)

    ssot["phase4_system_coherence"] = {
        "verdict": verdict,
        "tested_sha": counters["TESTED_SHA"],
        "generated_at": evidence["generated_at"],
        "counters_snapshot": {k: counters[k] for k in sorted(counters) if k != "TESTED_SHA"},
    }
    save_json(SSOT_PATH, ssot)

    print(json.dumps({"verdict": verdict, "counters": counters}, indent=2))
    return 0 if verdict == "CAPABILITY_SYSTEM_COHERENCE_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
