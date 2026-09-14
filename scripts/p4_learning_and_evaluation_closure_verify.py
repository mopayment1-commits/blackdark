#!/usr/bin/env python3
"""P4_LEARNING_AND_EVALUATION closure — authoritative 111-atomic reconciliation."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

POSTGRES = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)
ARTIFACT = Path("/opt/cursor/artifacts/TEMPORAL_P4_LEARNING_AND_EVALUATION_CLOSURE_EVIDENCE.json")
RTM_PATH = REPO / "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json"
P0_EVIDENCE = REPO / "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json"
P1_EVIDENCE = REPO / "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json"
P2_EVIDENCE = REPO / "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json"
P3_EVIDENCE = REPO / "TEMPORAL_P3_SHADOW_AND_REGIME_CLOSURE_EVIDENCE.json"

from blackdark.temporal.p4_closure_verification import evaluate_p4_closure_assertions
from blackdark.temporal.p4_requirement_registry import (
    P4_ATOMIC_REQUIREMENT_IDS,
    P4_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P4_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
    P4_REQUIREMENT_OWNERS,
)

OWNER_BASE_EVIDENCE: dict[str, str] = {
    "DEPENDENCE_AWARE_SAMPLING": "tests/test_temporal_p4_remaining_modules.py dependence tests",
    "WALK_FORWARD_VALIDATION": "tests/test_temporal_p4_remaining_modules.py walk-forward tests",
    "REPLAY_FIDELITY": "tests/test_temporal_p4_remaining_modules.py replay fidelity tests",
    "EXPERIENCE_COVERAGE": "tests/test_temporal_p4_remaining_modules.py experience coverage tests",
    "COUNTERFACTUAL_LAB": "tests/test_temporal_p4_remaining_modules.py counterfactual lab tests",
    "CONTAMINATION_REGISTRY": "tests/test_temporal_p4_remaining_modules.py contamination tests",
    "DRIFT": "tests/test_temporal_p4_remaining_modules.py P4 drift tests",
    "LEARNING_VALUE": "tests/test_temporal_p4_learning_value.py learning value tests",
    "CHAMPION_CHALLENGER": "tests/test_temporal_p4_champion_challenger.py champion/challenger tests",
    "CONTROLLED_LEARNING": "tests/test_temporal_p4_controlled_learning.py controlled learning tests",
    "CROSS_CUTTING_GOVERNANCE": "blackdark/temporal/p4_closure_verification.py module surface probes",
}

RUNTIME_EVIDENCE_OVERRIDES: dict[str, str] = {
    "TEMP-AR-0073": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0073_dependence_integration_effective_independent",
    "TEMP-AR-0095": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0095_tuning_contamination_postgres_integration",
    "TEMP-AR-0188": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0188_learning_value_prioritization_integration",
    "TEMP-AR-0189": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0189_learning_value_does_not_replace_sampling",
    "TEMP-AR-0213": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0213_replay_fidelity_composite_integration",
    "TEMP-AR-0229": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0229_experience_coverage_composite_integration",
    "TEMP-AR-0234": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0234_controlled_learning_candidate_weights_integration",
    "TEMP-AR-0239": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0239_controlled_learning_promotion_gate_integration",
    "TEMP-AR-0313": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0313_drift_representativeness_invalidation_integration",
    "TEMP-AR-0322": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0322_contamination_reuse_visibility_postgres",
    "TEMP-AR-0323": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0323_claim_strength_reduction_integration",
    "TEMP-AR-0457": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0457_effective_independent_sample_count_integration",
    "TEMP-AR-0458": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0458_replay_fidelity_dimensions_visible_integration",
    "TEMP-AR-0459": "tests/test_temporal_p4_closure_runtime_e2e.py::test_temp_ar_0459_experience_coverage_weak_dimensions_visible",
}

P4_TEST_FILES = (
    "tests/test_temporal_p4_learning_value.py",
    "tests/test_temporal_p4_champion_challenger.py",
    "tests/test_temporal_p4_controlled_learning.py",
    "tests/test_temporal_p4_remaining_modules.py",
    "tests/test_temporal_p4_closure_runtime_e2e.py",
)


def _build_evidence_by_atomic(rtm_rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for aid in P4_ATOMIC_REQUIREMENT_IDS:
        row = rtm_rows[aid]
        owner = P4_REQUIREMENT_OWNERS[aid]
        evidence[aid] = {
            "evidence": RUNTIME_EVIDENCE_OVERRIDES.get(aid, OWNER_BASE_EVIDENCE.get(owner, "p4_closure_verification probes")),
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


async def _verify_postgres_contamination_roundtrip() -> dict[str, Any]:
    from uuid import uuid4

    from blackdark.data.db import get_session, get_session_factory, init_data_engine
    from blackdark.temporal.contamination_registry import (
        ContaminationEntry,
        ContaminationPurpose,
        ContaminationState,
    )
    from blackdark.temporal.persistence.postgres import PostgresContaminationRegistry

    import config
    import blackdark.data.db as db_module

    config.DATABASE_URL = POSTGRES
    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False
    await init_data_engine()

    t_start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    dataset_id = f"p4-close-{uuid4().hex[:8]}"

    async with get_session() as session:
        registry = PostgresContaminationRegistry(session)
        await registry.hydrate()
        await registry.record_exposure_persisted(
            ContaminationEntry(
                entry_id=str(uuid4()),
                dataset_id=dataset_id,
                window_start=t_start,
                window_end=t_start + timedelta(hours=1),
                usage_purpose=ContaminationPurpose.TUNING,
                model_version="m1",
                config_version="c1",
                dataset_version="d1",
                exposure_count=1,
                contamination_state=ContaminationState.EXPOSED,
                metadata={"probe": "p4_closure"},
            )
        )

    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False
    get_session_factory()
    await init_data_engine()

    async with get_session() as session:
        reloaded = PostgresContaminationRegistry(session)
        await reloaded.hydrate()
        gate = reloaded.check_evaluation_admission(
            dataset_id=dataset_id,
            window_start=t_start,
            window_end=t_start + timedelta(hours=1),
            model_version="m1",
            config_version="c1",
            dataset_version="d1",
            fail_closed=False,
        )

    return {
        "dataset_id": dataset_id,
        "prior_exposures": gate.prior_exposures,
        "contamination_state": gate.contamination_state.value,
        "roundtrip_ok": gate.prior_exposures >= 1,
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


async def main() -> int:
    with RTM_PATH.open(encoding="utf-8") as handle:
        rtm = json.load(handle)

    p4_rows = [row for row in rtm["rtm_rows"] if row["phase_allocation"] == "P4_LEARNING_AND_EVALUATION"]
    if len(p4_rows) != P4_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS:
        raise SystemExit(
            f"Expected {P4_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS} P4 atomics, found {len(p4_rows)}"
        )
    if set(P4_ATOMIC_REQUIREMENT_IDS) != {row["atomic_requirement_id"] for row in p4_rows}:
        raise SystemExit("P4 registry IDs do not match RTM phase allocation")

    rtm_by_id = {row["atomic_requirement_id"]: row for row in p4_rows}
    evidence_by_atomic = _build_evidence_by_atomic(rtm_by_id)

    p0_baseline = _baseline_closed(P0_EVIDENCE, ("P0_CLOSED",))
    p1_baseline = _baseline_closed(P1_EVIDENCE, ("PHASE_CLOSED",))
    p2_baseline = _baseline_closed(P2_EVIDENCE, ("PHASE_CLOSED",))
    p3_baseline = _baseline_closed(
        P3_EVIDENCE,
        ("PHASE_CLOSED", "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"),
    )
    p4_pytest = _run_pytest(P4_TEST_FILES)
    p3_regression = _run_pytest(
        (
            "tests/test_temporal_p3_shadow_and_regime.py",
            "tests/test_temporal_p3_closure_runtime_e2e.py",
        )
    )
    closure_probes = evaluate_p4_closure_assertions()

    postgres_p4: dict[str, Any]
    try:
        postgres_p4 = await _verify_postgres_contamination_roundtrip()
        postgres_ok = postgres_p4.get("roundtrip_ok") is True
    except Exception as exc:
        postgres_p4 = {"error": str(exc), "status": "FAILED"}
        postgres_ok = False

    reconciliation: list[dict[str, Any]] = []
    counts = {
        "VERIFIED": 0,
        "IMPLEMENTED_NOT_VERIFIED": 0,
        "NOT_IMPLEMENTED": 0,
        "EXTERNAL_RUNTIME_PENDING": 0,
    }

    postgres_integration_ids = {
        "TEMP-AR-0095",
        "TEMP-AR-0322",
    }

    for aid in sorted(P4_ATOMIC_REQUIREMENT_IDS):
        row = rtm_by_id[aid]
        evidence = evidence_by_atomic[aid]
        status = "VERIFIED"

        if aid in P4_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS:
            status = "EXTERNAL_RUNTIME_PENDING"
        elif not evidence:
            status = "NOT_IMPLEMENTED"
        elif not p4_pytest["passed"]:
            status = "IMPLEMENTED_NOT_VERIFIED"
        elif aid in postgres_integration_ids and not postgres_ok:
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
    if not p4_pytest["passed"]:
        defects.append("P4 focused pytest suite failed")
    if not p3_regression["passed"]:
        defects.append("P3 regression pytest failed")
    if not closure_probes["closure_assertions"].get("P4_CLOSED"):
        defects.append("P4 closure runtime probes failed")
    if not postgres_ok:
        defects.append("Postgres contamination registry round-trip not verified")

    if counts["NOT_IMPLEMENTED"] or counts["IMPLEMENTED_NOT_VERIFIED"] or defects:
        verdict = "PHASE_NOT_CLOSED"
    elif counts["EXTERNAL_RUNTIME_PENDING"]:
        verdict = "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"
    else:
        verdict = "PHASE_CLOSED"

    report = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "scope": "P4_LEARNING_AND_EVALUATION",
        "governing_sources": [
            "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md",
            "TEMPORAL_PRIMARY_REQUIREMENTS.json",
            "TEMPORAL_ATOMIC_REQUIREMENTS.json",
            "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json",
            "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P3_SHADOW_AND_REGIME_CLOSURE_EVIDENCE.json",
        ],
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "p0_baseline": p0_baseline,
        "p1_baseline": p1_baseline,
        "p2_baseline": p2_baseline,
        "p3_baseline": p3_baseline,
        "p4_atomics_total": P4_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "counts": counts,
        "defects_remaining": defects,
        "external_runtime_gates": {},
        "runtime_proofs": {
            "p4_pytest": p4_pytest,
            "p3_regression_pytest": p3_regression,
            "closure_probes": closure_probes,
            "postgres_contamination": postgres_p4,
        },
        "reconciliation": reconciliation,
        "final_verdict": verdict,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPO / "TEMPORAL_P4_LEARNING_AND_EVALUATION_CLOSURE_EVIDENCE.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "PHASE": "P4_LEARNING_AND_EVALUATION",
                "TOTAL_ATOMICS": P4_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
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
    raise SystemExit(asyncio.run(main()))
