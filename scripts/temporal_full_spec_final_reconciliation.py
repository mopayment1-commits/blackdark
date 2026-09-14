#!/usr/bin/env python3
"""Final full-spec reconciliation across all 455 canonical TEMP-AR-* atomics."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ARTIFACT = Path("/opt/cursor/artifacts/TEMPORAL_FULL_SPEC_FINAL_RECONCILIATION.json")
REPO_ARTIFACT = REPO / "TEMPORAL_FULL_SPEC_FINAL_RECONCILIATION.json"

GOVERNING_SPEC = REPO / "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md"
PRIMARY_PATH = REPO / "TEMPORAL_PRIMARY_REQUIREMENTS.json"
ATOMIC_PATH = REPO / "TEMPORAL_ATOMIC_REQUIREMENTS.json"
RTM_PATH = REPO / "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json"

PHASE_CLOSURE_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("P0_TEMPORAL_TRUTH_FOUNDATION", "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json", "scripts/p0_foundation_closure_verify.py"),
    ("P1_CANONICAL_EVENT_AND_REPLAY", "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json", "scripts/p1_canonical_event_and_replay_closure_verify.py"),
    ("P2_OUTCOME_AND_EVIDENCE", "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json", "scripts/p2_outcome_and_evidence_closure_verify.py"),
    ("P3_SHADOW_AND_REGIME", "TEMPORAL_P3_SHADOW_AND_REGIME_CLOSURE_EVIDENCE.json", "scripts/p3_shadow_and_regime_closure_verify.py"),
    ("P4_LEARNING_AND_EVALUATION", "TEMPORAL_P4_LEARNING_AND_EVALUATION_CLOSURE_EVIDENCE.json", "scripts/p4_learning_and_evaluation_closure_verify.py"),
    ("P5_USER_EVIDENCE_EXPERIENCE", "TEMPORAL_P5_USER_EVIDENCE_EXPERIENCE_CLOSURE_EVIDENCE.json", "scripts/p5_user_evidence_experience_closure_verify.py"),
    ("P6_OPERATIONAL_HARDENING", "TEMPORAL_P6_OPERATIONAL_HARDENING_CLOSURE_EVIDENCE.json", "scripts/p6_operational_hardening_closure_verify.py"),
    ("EXTERNAL_OR_LIVE_GATE", "TEMPORAL_EXTERNAL_OR_LIVE_GATE_CLOSURE_EVIDENCE.json", "scripts/external_or_live_gate_closure_verify.py"),
)

ACCEPTED_PHASE_VERDICTS: dict[str, tuple[str, ...]] = {
    "P0_TEMPORAL_TRUTH_FOUNDATION": ("P0_CLOSED",),
    "P1_CANONICAL_EVENT_AND_REPLAY": ("PHASE_CLOSED",),
    "P2_OUTCOME_AND_EVIDENCE": ("PHASE_CLOSED",),
    "P3_SHADOW_AND_REGIME": ("PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"),
    "P4_LEARNING_AND_EVALUATION": ("PHASE_CLOSED",),
    "P5_USER_EVIDENCE_EXPERIENCE": ("PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"),
    "P6_OPERATIONAL_HARDENING": ("PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"),
    "EXTERNAL_OR_LIVE_GATE": (
        "EXTERNAL_GATE_SCOPE_CLOSED",
        "EXTERNAL_GATE_SCOPE_CLOSED_WITH_PENDING_EVIDENCE",
    ),
}

EXTERNAL_GATE_REASON_DEFAULTS: dict[str, str] = {
    "TEMP-AR-0164": "requires real forward time passage between receipt issuance and outcome evaluation",
    "TEMP-AR-0261": "requires genuine forward evidence that historical output was live-issued",
    "TEMP-AR-0431": "EXTERNAL_ASSURANCE: independent verification required that document approval does not imply PASS_ENGINEERING",
    "TEMP-AR-0432": "EXTERNAL_ASSURANCE: independent verification required that PASS_ENGINEERING has its own implementation evidence and gates",
    "TEMP-AR-0433": "EXTERNAL_ASSURANCE: live production observation required for PASS_LIVE assurance claim",
    "TEMP-AR-0434": "EXTERNAL_ASSURANCE: independent audit required for ASSURANCE_READY assurance claim",
    "TEMP-AR-0435": "EXTERNAL_ASSURANCE: live production observation and independent audit required for PRODUCTION_ALIGNED",
    "TEMP-AR-0436": "EXTERNAL_ASSURANCE: independent verification audit required",
    "TEMP-AR-0460": "EXTERNAL_ASSURANCE: independent verification required that document approval does not imply PASS_LIVE",
    "TEMP-AR-0461": "EXTERNAL_ASSURANCE: independent verification required that document approval does not imply ASSURANCE_READY",
    "TEMP-AR-0462": "EXTERNAL_ASSURANCE: independent verification required that document approval does not imply PRODUCTION_ALIGNED",
    "TEMP-AR-0463": "EXTERNAL_ASSURANCE: independent verification required that document approval does not imply independent verification",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_verify(script: str) -> dict[str, Any]:
    cmd = [sys.executable, str(REPO / script)]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    return {
        "script": script,
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": proc.stdout.splitlines()[-8:] if proc.stdout else [],
        "stderr_tail": proc.stderr.splitlines()[-8:] if proc.stderr else [],
    }


def _collect_external_gate_reasons(phase_artifacts: dict[str, dict[str, Any]]) -> dict[str, str]:
    reasons: dict[str, str] = dict(EXTERNAL_GATE_REASON_DEFAULTS)
    for artifact in phase_artifacts.values():
        gates = artifact.get("external_runtime_gates") or {}
        for aid, info in gates.items():
            if isinstance(info, dict) and info.get("reason"):
                reasons[aid] = str(info["reason"])
    return reasons


def _external_gate_reason(
    aid: str,
    status: str,
    verification_method: str,
    external_gate_reasons: dict[str, str],
) -> str | None:
    if status != "EXTERNAL_RUNTIME_PENDING":
        return None
    return external_gate_reasons.get(aid) or (
        f"{verification_method} verification requires external/live/independent evidence not available in repository"
    )


def main() -> int:
    if not GOVERNING_SPEC.exists():
        raise SystemExit(f"Missing governing spec: {GOVERNING_SPEC}")

    primary = _load_json(PRIMARY_PATH)
    atomic = _load_json(ATOMIC_PATH)
    rtm = _load_json(RTM_PATH)

    primary_ids = {row["primary_id"] for row in primary["requirements"]}
    atomic_ids = [row["atomic_requirement_id"] for row in atomic["atomic_requirements"]]
    rtm_rows = rtm["rtm_rows"]
    rtm_ids = [row["atomic_requirement_id"] for row in rtm_rows]
    rtm_by_id = {row["atomic_requirement_id"]: row for row in rtm_rows}

    traceability_defects: list[str] = []
    evidence_contradictions: list[str] = []
    regression_failures: list[str] = []

    if len(atomic_ids) != 455:
        traceability_defects.append(f"TEMPORAL_ATOMIC_REQUIREMENTS.json has {len(atomic_ids)} atomics, expected 455")
    if len(rtm_ids) != 455:
        traceability_defects.append(f"RTM has {len(rtm_ids)} rows, expected 455")

    atomic_dupes = [aid for aid, count in Counter(atomic_ids).items() if count > 1]
    rtm_dupes = [aid for aid, count in Counter(rtm_ids).items() if count > 1]
    duplicates = sorted(set(atomic_dupes + rtm_dupes))

    atomic_set = set(atomic_ids)
    rtm_set = set(rtm_ids)
    orphans_atomic = sorted(atomic_set - rtm_set)
    orphans_rtm = sorted(rtm_set - atomic_set)
    orphans = sorted(set(orphans_atomic + orphans_rtm))

    if atomic_set != rtm_set:
        traceability_defects.append(
            f"Atomic/RTM ID set mismatch: only_atomic={len(atomic_set - rtm_set)} only_rtm={len(rtm_set - atomic_set)}"
        )

    for row in rtm_rows:
        pr = row["parent_primary_requirement_id"]
        if pr not in primary_ids:
            traceability_defects.append(f"{row['atomic_requirement_id']} references missing primary {pr}")

    phase_artifacts: dict[str, dict[str, Any]] = {}
    merged_status: dict[str, str] = {}
    merged_rows: dict[str, dict[str, Any]] = {}
    phase_by_atomic: dict[str, str] = {}

    for phase, artifact_name, script in PHASE_CLOSURE_SOURCES:
        artifact_path = REPO / artifact_name
        if not artifact_path.exists():
            traceability_defects.append(f"Missing closure artifact for {phase}: {artifact_name}")
            continue
        artifact = _load_json(artifact_path)
        phase_artifacts[phase] = artifact
        verdict = artifact.get("final_verdict")
        if verdict not in ACCEPTED_PHASE_VERDICTS[phase]:
            evidence_contradictions.append(
                f"{artifact_name} final_verdict={verdict!r} not in accepted {ACCEPTED_PHASE_VERDICTS[phase]}"
            )
        reconciliation = artifact.get("reconciliation", [])
        artifact_ids = {row["atomic_requirement_id"] for row in reconciliation}
        expected_phase_ids = {
            aid for aid, row in rtm_by_id.items() if row["phase_allocation"] == phase
        }
        if artifact_ids != expected_phase_ids:
            missing = sorted(expected_phase_ids - artifact_ids)
            extra = sorted(artifact_ids - expected_phase_ids)
            if missing:
                traceability_defects.append(f"{phase} artifact missing atomics: {missing[:5]}{'...' if len(missing)>5 else ''}")
            if extra:
                traceability_defects.append(f"{phase} artifact has extra atomics: {extra[:5]}{'...' if len(extra)>5 else ''}")

        for row in reconciliation:
            aid = row["atomic_requirement_id"]
            status = row["status"]
            rtm_phase = rtm_by_id[aid]["phase_allocation"]
            if row.get("phase_allocation") and row["phase_allocation"] != rtm_phase:
                evidence_contradictions.append(
                    f"{aid}: artifact phase {row['phase_allocation']} != RTM phase {rtm_phase}"
                )
            if aid in merged_status and merged_status[aid] != status:
                evidence_contradictions.append(
                    f"{aid}: conflicting status {merged_status[aid]} vs {status} across artifacts"
                )
            merged_status[aid] = status
            merged_rows[aid] = row
            phase_by_atomic[aid] = phase

    unaccounted = sorted(rtm_set - set(merged_status))
    if unaccounted:
        traceability_defects.append(f"Unaccounted atomics: {unaccounted[:10]}{'...' if len(unaccounted)>10 else ''}")

    external_gate_reasons = _collect_external_gate_reasons(phase_artifacts)

    atomics: list[dict[str, Any]] = []
    counts = Counter(
        {
            "VERIFIED": 0,
            "IMPLEMENTED_NOT_VERIFIED": 0,
            "NOT_IMPLEMENTED": 0,
            "EXTERNAL_RUNTIME_PENDING": 0,
        }
    )

    for aid in sorted(rtm_set):
        rtm_row = rtm_by_id[aid]
        closure_row = merged_rows.get(aid, {})
        status = merged_status.get(aid, "NOT_IMPLEMENTED")
        counts[status] += 1

        verification_method = rtm_row.get("verification_method", "")
        if status == "VERIFIED" and verification_method == "EXTERNAL_ASSURANCE":
            evidence_contradictions.append(
                f"{aid}: marked VERIFIED but verification_method is EXTERNAL_ASSURANCE"
            )

        atomics.append(
            {
                "atomic_requirement_id": aid,
                "parent_primary_requirement_id": rtm_row["parent_primary_requirement_id"],
                "rtm_phase": rtm_row["phase_allocation"],
                "closure_phase_artifact": phase_by_atomic.get(aid),
                "status": status,
                "implementation_evidence": closure_row.get("evidence"),
                "verification_evidence": closure_row.get("evidence_tests") or verification_method,
                "verification_method": verification_method,
                "atomic_obligation": rtm_row.get("atomic_obligation"),
                "external_gate_reason": _external_gate_reason(
                    aid, status, verification_method, external_gate_reasons
                ),
            }
        )

    verify_results = [_run_verify(script) for _, _, script in PHASE_CLOSURE_SOURCES]
    for result in verify_results:
        if not result["passed"]:
            regression_failures.append(f"{result['script']} exit_code={result['exit_code']}")

    accounted_for = len(merged_status)
    total_atomics = 455

    if accounted_for != total_atomics:
        traceability_defects.append(f"ACCOUNTED_FOR={accounted_for} != TOTAL_ATOMICS={total_atomics}")

    status_sum = sum(counts.values())
    if status_sum != total_atomics:
        traceability_defects.append(f"Status sum {status_sum} != {total_atomics}")

    if (
        counts["VERIFIED"] == total_atomics
        and not duplicates
        and not orphans
        and not traceability_defects
        and not evidence_contradictions
        and not regression_failures
    ):
        final_verdict = "FULL_SPEC_CLOSED_AND_VERIFIED"
    elif (
        accounted_for == total_atomics
        and counts["NOT_IMPLEMENTED"] == 0
        and counts["IMPLEMENTED_NOT_VERIFIED"] == 0
        and not duplicates
        and not orphans
        and not traceability_defects
        and not evidence_contradictions
        and not regression_failures
    ):
        final_verdict = "FULL_SPEC_ENGINEERING_CLOSED_WITH_EXTERNAL_ASSURANCE_PENDING"
    else:
        final_verdict = "FULL_SPEC_NOT_CLOSED"

    external_pending = [
        {
            "atomic_requirement_id": row["atomic_requirement_id"],
            "rtm_phase": row["rtm_phase"],
            "external_gate_reason": row["external_gate_reason"],
        }
        for row in atomics
        if row["status"] == "EXTERNAL_RUNTIME_PENDING"
    ]

    report = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "scope": "FULL_SPEC_FINAL_RECONCILIATION",
        "governing_sources": [
            str(GOVERNING_SPEC.relative_to(REPO)),
            PRIMARY_PATH.name,
            ATOMIC_PATH.name,
            RTM_PATH.name,
            *[artifact for _, artifact, _ in PHASE_CLOSURE_SOURCES],
        ],
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "summary": {
            "TOTAL_ATOMICS": total_atomics,
            "ACCOUNTED_FOR": accounted_for,
            "VERIFIED": counts["VERIFIED"],
            "IMPLEMENTED_NOT_VERIFIED": counts["IMPLEMENTED_NOT_VERIFIED"],
            "NOT_IMPLEMENTED": counts["NOT_IMPLEMENTED"],
            "EXTERNAL_RUNTIME_PENDING": counts["EXTERNAL_RUNTIME_PENDING"],
            "DUPLICATES": len(duplicates),
            "ORPHANS": len(orphans),
            "TRACEABILITY_DEFECTS": len(traceability_defects),
            "EVIDENCE_CONTRADICTIONS": len(evidence_contradictions),
            "REGRESSION_FAILURES": len(regression_failures),
            "final_verdict": final_verdict,
        },
        "phase_closure_verdicts": {
            phase: {
                "artifact": artifact,
                "final_verdict": phase_artifacts.get(phase, {}).get("final_verdict"),
                "counts": phase_artifacts.get(phase, {}).get("counts"),
            }
            for phase, artifact, _ in PHASE_CLOSURE_SOURCES
        },
        "duplicate_ids": duplicates,
        "orphan_ids": orphans,
        "traceability_defects": traceability_defects,
        "evidence_contradictions": evidence_contradictions,
        "regression_failures": regression_failures,
        "regression_proofs": verify_results,
        "external_pending_atomics": external_pending,
        "atomics": atomics,
        "verification_command": "python3 scripts/temporal_full_spec_final_reconciliation.py",
        "final_verdict": final_verdict,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPO_ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = report["summary"]
    print(
        json.dumps(
            {
                "TOTAL_ATOMICS": summary["TOTAL_ATOMICS"],
                "ACCOUNTED_FOR": summary["ACCOUNTED_FOR"],
                "VERIFIED": summary["VERIFIED"],
                "IMPLEMENTED_NOT_VERIFIED": summary["IMPLEMENTED_NOT_VERIFIED"],
                "NOT_IMPLEMENTED": summary["NOT_IMPLEMENTED"],
                "EXTERNAL_RUNTIME_PENDING": summary["EXTERNAL_RUNTIME_PENDING"],
                "DUPLICATES": summary["DUPLICATES"],
                "ORPHANS": summary["ORPHANS"],
                "TRACEABILITY_DEFECTS": summary["TRACEABILITY_DEFECTS"],
                "EVIDENCE_CONTRADICTIONS": summary["EVIDENCE_CONTRADICTIONS"],
                "REGRESSION_FAILURES": summary["REGRESSION_FAILURES"],
                "final_verdict": final_verdict,
            },
            indent=2,
        )
    )
    return 0 if final_verdict != "FULL_SPEC_NOT_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
