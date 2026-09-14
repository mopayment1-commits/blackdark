#!/usr/bin/env python3
"""P5_USER_EVIDENCE_EXPERIENCE closure — authoritative 43-atomic reconciliation."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ARTIFACT = Path("/opt/cursor/artifacts/TEMPORAL_P5_USER_EVIDENCE_EXPERIENCE_CLOSURE_EVIDENCE.json")
RTM_PATH = REPO / "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json"
P0_EVIDENCE = REPO / "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json"
P1_EVIDENCE = REPO / "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json"
P2_EVIDENCE = REPO / "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json"
P3_EVIDENCE = REPO / "TEMPORAL_P3_SHADOW_AND_REGIME_CLOSURE_EVIDENCE.json"
P4_EVIDENCE = REPO / "TEMPORAL_P4_LEARNING_AND_EVALUATION_CLOSURE_EVIDENCE.json"

from blackdark.temporal.p5_closure_verification import (
    evaluate_p5_closure_assertions,
    probe_temp_ar_0261_status,
)
from blackdark.temporal.p5_requirement_registry import (
    P5_ATOMIC_REQUIREMENT_IDS,
    P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P5_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
    P5_REQUIREMENT_OWNERS,
)

OWNER_BASE_EVIDENCE: dict[str, str] = {
    "MARKET_TIME_MACHINE": "tests/test_temporal_p5_market_time_machine.py",
    "PUBLIC_EVIDENCE": "tests/test_temporal_p5_public_evidence.py",
    "USER_BEHAVIORAL_LEARNING": "tests/test_temporal_p5_user_behavioral_learning.py",
    "CROSS_CUTTING_GOVERNANCE": "blackdark/temporal/p5_closure_verification.py module probes",
}

RUNTIME_EVIDENCE_OVERRIDES: dict[str, str] = {
    "TEMP-AR-0255": "tests/test_temporal_p5_market_time_machine.py::test_temp_ar_0255_replay_internal_mode",
    "TEMP-AR-0259": "tests/test_temporal_p5_closure_runtime_e2e.py::test_temp_ar_0259_user_facing_experience_runtime_integration",
    "TEMP-AR-0261": "blackdark/temporal/market_time_machine.py + probe_temp_ar_0261_status (external gate)",
    "TEMP-AR-0262": "tests/test_temporal_p5_public_evidence.py::test_temp_ar_0262_public_ledger_maturity_required",
    "TEMP-AR-0267": "tests/test_temporal_p5_public_evidence.py::test_temp_ar_0267_regime_distribution",
    "TEMP-AR-0263": "tests/test_temporal_p5_closure_runtime_e2e.py::test_temp_ar_0263_public_disclosure_runtime_integration",
    "TEMP-AR-0352": "tests/test_temporal_p5_closure_runtime_e2e.py::test_temp_ar_0352_behavioral_learning_runtime_integration",
    "TEMP-AR-0357": "tests/test_temporal_p5_user_behavioral_learning.py::test_temp_ar_0357_deletion_rights",
    "TEMP-AR-0360": "tests/test_temporal_p5_user_behavioral_learning.py::test_temp_ar_0360_buy_click_not_outcome_proof",
}

P5_TEST_FILES = (
    "tests/test_temporal_p5_market_time_machine.py",
    "tests/test_temporal_p5_public_evidence.py",
    "tests/test_temporal_p5_user_behavioral_learning.py",
    "tests/test_temporal_p5_closure.py",
    "tests/test_temporal_p5_closure_runtime_e2e.py",
)


def _build_evidence_by_atomic(rtm_rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for aid in P5_ATOMIC_REQUIREMENT_IDS:
        row = rtm_rows[aid]
        owner = P5_REQUIREMENT_OWNERS[aid]
        evidence[aid] = {
            "evidence": RUNTIME_EVIDENCE_OVERRIDES.get(aid, OWNER_BASE_EVIDENCE.get(owner, "p5_closure_verification probes")),
            "tests": row["verification_method"],
        }
    return evidence


def _run_pytest(paths: tuple[str, ...]) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", *paths, "-q", "--tb=no"]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    tail = proc.stdout.splitlines()[-3:] if proc.stdout else []
    passed_line = next((line for line in proc.stdout.splitlines() if "passed" in line), "")
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "summary": passed_line,
        "tail": tail,
    }


def _baseline_closed(path: Path, expected_verdicts: tuple[str, ...]) -> dict[str, Any]:
    if not path.exists():
        return {"closed": False, "reason": f"{path.name} missing"}
    data = json.loads(path.read_text(encoding="utf-8"))
    verdict = data.get("final_verdict")
    return {
        "closed": verdict in expected_verdicts,
        "final_verdict": verdict,
        "verified": data.get("counts", {}).get("VERIFIED"),
    }


def main() -> int:
    with RTM_PATH.open(encoding="utf-8") as handle:
        rtm = json.load(handle)

    p5_rows = [row for row in rtm["rtm_rows"] if row["phase_allocation"] == "P5_USER_EVIDENCE_EXPERIENCE"]
    if len(p5_rows) != P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS:
        raise SystemExit(
            f"Expected {P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS} P5 atomics, found {len(p5_rows)}"
        )
    if set(P5_ATOMIC_REQUIREMENT_IDS) != {row["atomic_requirement_id"] for row in p5_rows}:
        raise SystemExit("P5 registry IDs do not match RTM phase allocation")

    rtm_by_id = {row["atomic_requirement_id"]: row for row in p5_rows}
    evidence_by_atomic = _build_evidence_by_atomic(rtm_by_id)

    p0_baseline = _baseline_closed(P0_EVIDENCE, ("P0_CLOSED",))
    p1_baseline = _baseline_closed(P1_EVIDENCE, ("PHASE_CLOSED",))
    p2_baseline = _baseline_closed(P2_EVIDENCE, ("PHASE_CLOSED",))
    p3_baseline = _baseline_closed(
        P3_EVIDENCE,
        ("PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"),
    )
    p4_baseline = _baseline_closed(P4_EVIDENCE, ("PHASE_CLOSED",))
    p5_pytest = _run_pytest(P5_TEST_FILES)
    p4_regression = _run_pytest(
        (
            "tests/test_temporal_p4_learning_value.py",
            "tests/test_temporal_p4_remaining_modules.py",
        )
    )
    closure_probes = evaluate_p5_closure_assertions()
    temp_ar_0261 = probe_temp_ar_0261_status()

    reconciliation: list[dict[str, Any]] = []
    counts = {
        "VERIFIED": 0,
        "IMPLEMENTED_NOT_VERIFIED": 0,
        "NOT_IMPLEMENTED": 0,
        "EXTERNAL_RUNTIME_PENDING": 0,
    }
    external_gates: dict[str, Any] = {}

    for aid in sorted(P5_ATOMIC_REQUIREMENT_IDS):
        row = rtm_by_id[aid]
        evidence = evidence_by_atomic[aid]
        status = "VERIFIED"

        if aid in P5_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS:
            if temp_ar_0261.get("external_evidence_pending") and not temp_ar_0261.get("forward_issuance_verified"):
                status = "EXTERNAL_RUNTIME_PENDING"
                external_gates[aid] = {
                    "reason": "requires genuine forward evidence that historical output was live-issued",
                    "local_engineering_complete": temp_ar_0261.get("local_engineering_complete"),
                    "forward_issuance_verified": temp_ar_0261.get("forward_issuance_verified"),
                }
            elif not temp_ar_0261.get("local_engineering_complete"):
                status = "IMPLEMENTED_NOT_VERIFIED"
        elif not evidence:
            status = "NOT_IMPLEMENTED"
        elif not p5_pytest["passed"]:
            status = "IMPLEMENTED_NOT_VERIFIED"

        counts[status] += 1
        reconciliation.append(
            {
                "atomic_requirement_id": aid,
                "parent_primary_requirement_id": row["parent_primary_requirement_id"],
                "phase_allocation": row["phase_allocation"],
                "logical_owner": row.get("logical_owner"),
                "verification_method": row["verification_method"],
                "atomic_obligation": row["atomic_obligation"],
                "status": status,
                "evidence": evidence["evidence"],
                "evidence_tests": evidence["tests"],
            }
        )

    defects: list[str] = []
    if not p0_baseline.get("closed"):
        defects.append("P0 baseline not closed")
    if not p1_baseline.get("closed"):
        defects.append("P1 baseline not closed")
    if not p2_baseline.get("closed"):
        defects.append("P2 baseline not closed")
    if not p3_baseline.get("closed"):
        defects.append("P3 baseline not closed")
    if not p4_baseline.get("closed"):
        defects.append("P4 baseline not closed")
    if not p5_pytest["passed"]:
        defects.append("P5 focused pytest suite failed")
    if not p4_regression["passed"]:
        defects.append("P4 regression pytest failed")
    if not closure_probes["closure_assertions"].get("P5_CLOSED"):
        defects.append("P5 closure runtime probes failed")

    if counts["NOT_IMPLEMENTED"] or counts["IMPLEMENTED_NOT_VERIFIED"] or defects:
        verdict = "PHASE_NOT_CLOSED"
    elif counts["EXTERNAL_RUNTIME_PENDING"]:
        verdict = "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"
    else:
        verdict = "PHASE_CLOSED"

    report = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "scope": "P5_USER_EVIDENCE_EXPERIENCE",
        "governing_sources": [
            "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md",
            "TEMPORAL_PRIMARY_REQUIREMENTS.json",
            "TEMPORAL_ATOMIC_REQUIREMENTS.json",
            "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json",
            "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P3_SHADOW_AND_REGIME_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P4_LEARNING_AND_EVALUATION_CLOSURE_EVIDENCE.json",
        ],
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "p0_baseline": p0_baseline,
        "p1_baseline": p1_baseline,
        "p2_baseline": p2_baseline,
        "p3_baseline": p3_baseline,
        "p4_baseline": p4_baseline,
        "p5_atomics_total": P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "counts": counts,
        "defects_remaining": defects,
        "external_runtime_gates": external_gates,
        "runtime_proofs": {
            "p5_pytest": p5_pytest,
            "p4_regression_pytest": p4_regression,
            "closure_probes": closure_probes,
            "temp_ar_0261": temp_ar_0261,
        },
        "reconciliation": reconciliation,
        "final_verdict": verdict,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPO / "TEMPORAL_P5_USER_EVIDENCE_EXPERIENCE_CLOSURE_EVIDENCE.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "PHASE": "P5_USER_EVIDENCE_EXPERIENCE",
                "TOTAL_ATOMICS": P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
                "VERIFIED": counts["VERIFIED"],
                "IMPLEMENTED_NOT_VERIFIED": counts["IMPLEMENTED_NOT_VERIFIED"],
                "NOT_IMPLEMENTED": counts["NOT_IMPLEMENTED"],
                "EXTERNAL_RUNTIME_PENDING": counts["EXTERNAL_RUNTIME_PENDING"],
                "DEFECTS": len(defects),
                "final_verdict": verdict,
            },
            indent=2,
        )
    )
    return 0 if verdict in {"PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
