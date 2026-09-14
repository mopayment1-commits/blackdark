#!/usr/bin/env python3
"""EXTERNAL_OR_LIVE_GATE closure — authoritative 10-atomic reconciliation."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ARTIFACT = Path("/opt/cursor/artifacts/TEMPORAL_EXTERNAL_OR_LIVE_GATE_CLOSURE_EVIDENCE.json")
RTM_PATH = REPO / "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json"
P0_EVIDENCE = REPO / "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json"
P1_EVIDENCE = REPO / "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json"
P2_EVIDENCE = REPO / "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json"
P3_EVIDENCE = REPO / "TEMPORAL_P3_SHADOW_AND_REGIME_CLOSURE_EVIDENCE.json"
P4_EVIDENCE = REPO / "TEMPORAL_P4_LEARNING_AND_EVALUATION_CLOSURE_EVIDENCE.json"
P5_EVIDENCE = REPO / "TEMPORAL_P5_USER_EVIDENCE_EXPERIENCE_CLOSURE_EVIDENCE.json"
P6_EVIDENCE = REPO / "TEMPORAL_P6_OPERATIONAL_HARDENING_CLOSURE_EVIDENCE.json"

from blackdark.temporal.external_gate_closure_verification import evaluate_external_gate_closure_assertions
from blackdark.temporal.external_gate_requirement_registry import (
    EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS,
    EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS,
    EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS,
    EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    EXTERNAL_GATE_EXTERNAL_ASSURANCE_ATOMIC_IDS,
    EXTERNAL_GATE_REQUIREMENT_OWNERS,
)

OWNER_BASE_EVIDENCE: dict[str, str] = {
    "CROSS_CUTTING_GOVERNANCE": "blackdark/temporal/external_gate_closure_verification.py module probes",
}

RUNTIME_EVIDENCE_OVERRIDES: dict[str, str] = {
    "TEMP-AR-0431": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0431_document_approval_not_pass_engineering",
    "TEMP-AR-0432": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0432_pass_engineering_requires_own_evidence",
    "TEMP-AR-0433": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0433_pass_live_requires_external_evidence",
    "TEMP-AR-0434": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0434_assurance_ready_requires_independent_audit",
    "TEMP-AR-0435": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0435_production_aligned_requires_external_evidence",
    "TEMP-AR-0436": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0436_independent_verification_requires_audit",
    "TEMP-AR-0460": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0460_document_approval_not_pass_live",
    "TEMP-AR-0461": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0461_document_approval_not_assurance_ready",
    "TEMP-AR-0462": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0462_document_approval_not_production_aligned",
    "TEMP-AR-0463": "tests/test_temporal_external_gate_assurance.py::test_temp_ar_0463_document_approval_not_independent_verification",
}

EXTERNAL_GATE_TEST_FILES = (
    "tests/test_temporal_external_gate_assurance.py",
    "tests/test_temporal_external_gate_closure.py",
)


def _build_evidence_by_atomic(rtm_rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for aid in EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS:
        row = rtm_rows[aid]
        owner = EXTERNAL_GATE_REQUIREMENT_OWNERS[aid]
        evidence[aid] = {
            "evidence": RUNTIME_EVIDENCE_OVERRIDES.get(
                aid,
                OWNER_BASE_EVIDENCE.get(owner, "external_gate_closure_verification probes"),
            ),
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


def _classify_atomic_status(
    aid: str,
    *,
    pytest_passed: bool,
    per_atomic_probe: dict[str, Any],
) -> str:
    if aid not in EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS:
        return "NOT_IMPLEMENTED"

    if not per_atomic_probe.get("local_engineering_complete"):
        return "NOT_IMPLEMENTED"

    if not pytest_passed:
        return "IMPLEMENTED_NOT_VERIFIED"

    # EXTERNAL_ASSURANCE verification cannot be closed with repository-only evidence.
    if aid in EXTERNAL_GATE_EXTERNAL_ASSURANCE_ATOMIC_IDS:
        if per_atomic_probe.get("external_assurance_verified"):
            return "VERIFIED"
        return "EXTERNAL_RUNTIME_PENDING"

    return "IMPLEMENTED_NOT_VERIFIED"


def main() -> int:
    with RTM_PATH.open(encoding="utf-8") as handle:
        rtm = json.load(handle)

    gate_rows = [row for row in rtm["rtm_rows"] if row["phase_allocation"] == "EXTERNAL_OR_LIVE_GATE"]
    if len(gate_rows) != EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS:
        raise SystemExit(
            f"Expected {EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS} EXTERNAL_OR_LIVE_GATE atomics, "
            f"found {len(gate_rows)}"
        )
    if set(EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS) != {row["atomic_requirement_id"] for row in gate_rows}:
        raise SystemExit("EXTERNAL_OR_LIVE_GATE registry IDs do not match RTM phase allocation")

    rtm_by_id = {row["atomic_requirement_id"]: row for row in gate_rows}
    evidence_by_atomic = _build_evidence_by_atomic(rtm_by_id)

    p0_baseline = _baseline_closed(P0_EVIDENCE, ("P0_CLOSED",))
    p1_baseline = _baseline_closed(P1_EVIDENCE, ("PHASE_CLOSED",))
    p2_baseline = _baseline_closed(P2_EVIDENCE, ("PHASE_CLOSED",))
    p3_baseline = _baseline_closed(
        P3_EVIDENCE,
        ("PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"),
    )
    p4_baseline = _baseline_closed(P4_EVIDENCE, ("PHASE_CLOSED",))
    p5_baseline = _baseline_closed(
        P5_EVIDENCE,
        ("PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"),
    )
    p6_baseline = _baseline_closed(P6_EVIDENCE, ("PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"))
    gate_pytest = _run_pytest(EXTERNAL_GATE_TEST_FILES)
    p6_regression = _run_pytest(("tests/test_temporal_p6_closure.py",))
    closure_probes = evaluate_external_gate_closure_assertions(
        runtime_signals={"p6_baseline_closed": p6_baseline.get("closed", False)}
    )
    per_atomic_probe = closure_probes["per_atomic_status"]

    reconciliation: list[dict[str, Any]] = []
    counts = {
        "VERIFIED": 0,
        "IMPLEMENTED_NOT_VERIFIED": 0,
        "NOT_IMPLEMENTED": 0,
        "EXTERNAL_RUNTIME_PENDING": 0,
    }

    for aid in sorted(EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS):
        row = rtm_by_id[aid]
        evidence = evidence_by_atomic[aid]
        probe = per_atomic_probe[aid]
        status = _classify_atomic_status(
            aid,
            pytest_passed=gate_pytest["passed"],
            per_atomic_probe=probe,
        )
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
                "probe": probe,
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
    if not p5_baseline.get("closed"):
        defects.append("P5 baseline not closed")
    if not p6_baseline.get("closed"):
        defects.append("P6 baseline not closed")
    if not gate_pytest["passed"]:
        defects.append("EXTERNAL_OR_LIVE_GATE focused pytest suite failed")
    if not p6_regression["passed"]:
        defects.append("P6 regression pytest failed")
    if not closure_probes["closure_assertions"].get("EXTERNAL_GATE_SCOPE_CLOSED"):
        defects.append("EXTERNAL_OR_LIVE_GATE closure runtime probes failed")

    total_accounted = sum(counts.values())
    if total_accounted != EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS:
        defects.append(
            f"Atomic status accounting mismatch: {total_accounted} != {EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS}"
        )

    if counts["NOT_IMPLEMENTED"] or counts["IMPLEMENTED_NOT_VERIFIED"] or defects:
        verdict = "EXTERNAL_GATE_SCOPE_NOT_CLOSED"
    elif counts["EXTERNAL_RUNTIME_PENDING"]:
        verdict = "EXTERNAL_GATE_SCOPE_CLOSED_WITH_PENDING_EVIDENCE"
    else:
        verdict = "EXTERNAL_GATE_SCOPE_CLOSED"

    report = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "scope": "EXTERNAL_OR_LIVE_GATE",
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
            "TEMPORAL_P5_USER_EVIDENCE_EXPERIENCE_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P6_OPERATIONAL_HARDENING_CLOSURE_EVIDENCE.json",
        ],
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "p0_baseline": p0_baseline,
        "p1_baseline": p1_baseline,
        "p2_baseline": p2_baseline,
        "p3_baseline": p3_baseline,
        "p4_baseline": p4_baseline,
        "p5_baseline": p5_baseline,
        "p6_baseline": p6_baseline,
        "external_gate_atomics_total": EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "document_approval_prohibition_ids": list(EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS),
        "evidence_requirement_ids": list(EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS),
        "counts": counts,
        "defects_remaining": defects,
        "runtime_proofs": {
            "external_gate_pytest": gate_pytest,
            "p6_regression_pytest": p6_regression,
            "closure_probes": closure_probes,
        },
        "reconciliation": reconciliation,
        "final_verdict": verdict,
        "verification_command": "python3 scripts/external_or_live_gate_closure_verify.py",
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPO / "TEMPORAL_EXTERNAL_OR_LIVE_GATE_CLOSURE_EVIDENCE.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "PHASE": "EXTERNAL_OR_LIVE_GATE",
                "TOTAL_ATOMICS": EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
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
    return 0 if verdict in {
        "EXTERNAL_GATE_SCOPE_CLOSED",
        "EXTERNAL_GATE_SCOPE_CLOSED_WITH_PENDING_EVIDENCE",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
