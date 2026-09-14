#!/usr/bin/env python3
"""P2_OUTCOME_AND_EVIDENCE closure — authoritative 103-atomic reconciliation."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

POSTGRES = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)
ARTIFACT = Path("/opt/cursor/artifacts/TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json")
RTM_PATH = REPO / "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json"
P0_EVIDENCE = REPO / "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json"
P1_EVIDENCE = REPO / "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json"

from blackdark.temporal.p2_requirement_registry import (
    P2_ATOMIC_REQUIREMENT_IDS,
    P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P2_REQUIREMENT_OWNERS,
)

OWNER_BASE_EVIDENCE: dict[str, str] = {
    "OUTCOME_FACTORY": "tests/test_temporal_p2_outcome_and_evidence.py outcome factory tests",
    "OUTCOME_QUALITY": "tests/test_temporal_p2_outcome_and_evidence.py outcome quality tests",
    "EVIDENCE_PROVENANCE": "tests/test_temporal_p2_outcome_and_evidence.py evidence provenance tests",
    "RETENTION_POLICY": "tests/test_temporal_p2_outcome_and_evidence.py retention policy tests",
    "SOURCE_RIGHTS": "tests/test_temporal_p2_outcome_and_evidence.py source rights tests",
    "SOURCE_QUALITY": "tests/test_temporal_p2_outcome_and_evidence.py source quality tests",
    "REPRODUCIBILITY": "tests/test_temporal_p2_outcome_and_evidence.py reproducibility manifest tests",
    "CROSS_CUTTING_GOVERNANCE": "tests/test_temporal_p2_outcome_and_evidence.py P2 pipeline integration",
}

RUNTIME_EVIDENCE_OVERRIDES: dict[str, str] = {
    "TEMP-AR-0103": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0103_calibration_error_empirical",
    "TEMP-AR-0113": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0113_market_regime_empirical",
    "TEMP-AR-0115": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0115_independent_evaluator_integration",
    "TEMP-AR-0145": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0145_evidence_version_scoped_integration",
    "TEMP-AR-0146": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0146_evidence_methodology_preserved_integration",
    "TEMP-AR-0147": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0147_evidence_timestamps_preserved_integration",
    "TEMP-AR-0148": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0148_evaluator_identity_preserved_integration",
    "TEMP-AR-0150": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0150_evidence_limitations_preserved_integration",
    "TEMP-AR-0193": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0193_warm_tier_replay_retrieval",
    "TEMP-AR-0196": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0196_compression_performance",
    "TEMP-AR-0202": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0202_reproducible_retrieval_integration",
    "TEMP-AR-0303": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0303_source_quality_replay_fidelity",
    "TEMP-AR-0336": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0336_material_results_reproducible_integration",
    "TEMP-AR-0337": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0337_reproducibility_limitations_marked_integration",
    "TEMP-AR-0379": "tests/test_temporal_p2_closure_runtime_e2e.py::test_temp_ar_0379_reproducibility_manifest_integration",
}

P2_TEST_FILES = (
    "tests/test_temporal_p2_outcome_and_evidence.py",
    "tests/test_temporal_p2_closure_runtime_e2e.py",
)


def _build_evidence_by_atomic(rtm_rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for aid in P2_ATOMIC_REQUIREMENT_IDS:
        row = rtm_rows[aid]
        owner = P2_REQUIREMENT_OWNERS[aid]
        evidence[aid] = {
            "evidence": RUNTIME_EVIDENCE_OVERRIDES.get(aid, OWNER_BASE_EVIDENCE[owner]),
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


async def _verify_postgres_p2_spine() -> dict[str, Any]:
    from blackdark.data.db import get_session, get_session_factory
    from blackdark.data.temporal_repository import get_evidence_record
    from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
    from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine

    import config
    import blackdark.data.db as db_module

    config.DATABASE_URL = POSTGRES
    db_module._engine = None
    db_module._session_factory = None
    if not db_module._schema_ready:
        from blackdark.data.db import init_data_engine

        await init_data_engine()

    suffix = uuid.uuid4().hex[:8]
    sim = "2026-07-01T02:00:00Z"
    avail = "2026-07-01T01:00:00Z"
    sim_dt = datetime.fromisoformat("2026-07-01T02:00:00+00:00")
    idem = f"p2-closure-{suffix}"
    payload = {
        "entity_key": f"P2CLOSE-{suffix}",
        "event_type": "market_tick",
        "payload": {"price": "100"},
        "observation": build_observation_dict(
            event_time=sim,
            observed_time=sim,
            available_at=avail,
            ingested_at=avail,
            effective_at=sim,
            revised_at=avail,
        ),
        "provenance": build_provenance_dict(
            source="p2-closure",
            source_version="v1",
            dataset_version=f"ds-close-{suffix}",
            rights_or_provenance={"permitted_purpose": "historical_evaluation"},
        ),
    }
    async with get_session() as session:
        spine = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=payload,
                simulated_time=sim_dt,
                prediction={"direction": "hold"},
                confidence=0.5,
                abstention_state="abstain",
                subject_identity=f"P2CLOSE-{suffix}",
                input_identity=f"input-{suffix}",
                idempotency_key=idem,
            ),
        )
    assert spine.event_id
    assert spine.p2_metadata is not None
    assert spine.evidence_ids

    db_module._engine = None
    db_module._session_factory = None
    get_session_factory()

    async with get_session() as session:
        evidence = await get_evidence_record(session, spine.evidence_ids[0])

    return {
        "event_id": spine.event_id,
        "evidence_id": spine.evidence_ids[0],
        "evidence_class": evidence["evidence_class"] if evidence else None,
        "p2_metadata_present": spine.p2_metadata is not None,
        "reproducibility_run_id": spine.p2_metadata.get("reproducibility", {}).get("run_id"),
        "predictor_self_validation": spine.p2_metadata.get("predictor_self_validation"),
        "p2_pipeline_stage_completed": any(
            s.get("stage") == "p2_pipeline" and s.get("status") == "completed"
            for s in spine.observability.get("stages", [])
        ),
    }


def _baseline_closed(path: Path, expected_verdict: str) -> dict[str, Any]:
    if not path.exists():
        return {"closed": False, "reason": f"{path.name} missing"}
    data = json.loads(path.read_text(encoding="utf-8"))
    verdict = data.get("final_verdict")
    return {
        "closed": verdict == expected_verdict,
        "final_verdict": verdict,
        "verified": data.get("counts", {}).get("VERIFIED"),
    }


async def main() -> int:
    with RTM_PATH.open(encoding="utf-8") as handle:
        rtm = json.load(handle)

    p2_rows = [row for row in rtm["rtm_rows"] if row["phase_allocation"] == "P2_OUTCOME_AND_EVIDENCE"]
    if len(p2_rows) != P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS:
        raise SystemExit(
            f"Expected {P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS} P2 atomics, found {len(p2_rows)}"
        )
    if set(P2_ATOMIC_REQUIREMENT_IDS) != {row["atomic_requirement_id"] for row in p2_rows}:
        raise SystemExit("P2 registry IDs do not match RTM phase allocation")

    rtm_by_id = {row["atomic_requirement_id"]: row for row in p2_rows}
    evidence_by_atomic = _build_evidence_by_atomic(rtm_by_id)

    p0_baseline = _baseline_closed(P0_EVIDENCE, "P0_CLOSED")
    p1_baseline = _baseline_closed(P1_EVIDENCE, "PHASE_CLOSED")
    p2_pytest = _run_pytest(P2_TEST_FILES)
    p1_regression = _run_pytest(
        (
            "tests/test_temporal_p1_1_canonical_event_store.py",
            "tests/test_temporal_p1_2_deterministic_mass_replay.py",
            "tests/test_temporal_p1_3_remaining_replay_coverage.py",
            "tests/test_temporal_p1_closure_runtime_e2e.py",
        )
    )

    postgres_p2: dict[str, Any]
    try:
        postgres_p2 = await _verify_postgres_p2_spine()
        postgres_ok = (
            postgres_p2.get("p2_metadata_present")
            and postgres_p2.get("p2_pipeline_stage_completed")
            and postgres_p2.get("evidence_class") == "HISTORICAL_REPLAY"
            and postgres_p2.get("predictor_self_validation") is False
        )
    except Exception as exc:
        postgres_p2 = {"error": str(exc), "status": "FAILED"}
        postgres_ok = False

    reconciliation: list[dict[str, Any]] = []
    counts = {
        "VERIFIED": 0,
        "IMPLEMENTED_NOT_VERIFIED": 0,
        "NOT_IMPLEMENTED": 0,
        "EXTERNAL_RUNTIME_PENDING": 0,
    }

    runtime_atomics = set(RUNTIME_EVIDENCE_OVERRIDES)

    for aid in sorted(P2_ATOMIC_REQUIREMENT_IDS):
        row = rtm_by_id[aid]
        evidence = evidence_by_atomic[aid]
        status = "VERIFIED"

        if not evidence:
            status = "NOT_IMPLEMENTED"
        elif not p2_pytest["passed"]:
            status = "IMPLEMENTED_NOT_VERIFIED"
        elif aid in runtime_atomics and not postgres_ok and aid == "TEMP-AR-0379":
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
    if not p2_pytest["passed"]:
        defects.append("P2 focused pytest suite failed")
    if not p1_regression["passed"]:
        defects.append("P1 regression pytest failed")
    if not postgres_ok:
        defects.append("Postgres P2 spine/evidence round-trip not verified")

    external_gates: dict[str, Any] = {}

    if counts["NOT_IMPLEMENTED"] or counts["IMPLEMENTED_NOT_VERIFIED"] or defects:
        if counts["EXTERNAL_RUNTIME_PENDING"] and not counts["NOT_IMPLEMENTED"] and not counts["IMPLEMENTED_NOT_VERIFIED"]:
            verdict = "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"
        else:
            verdict = "PHASE_NOT_CLOSED"
    elif counts["EXTERNAL_RUNTIME_PENDING"]:
        verdict = "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"
    else:
        verdict = "PHASE_CLOSED"

    report = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "scope": "P2_OUTCOME_AND_EVIDENCE",
        "governing_sources": [
            "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md",
            "TEMPORAL_PRIMARY_REQUIREMENTS.json",
            "TEMPORAL_ATOMIC_REQUIREMENTS.json",
            "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json",
            "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json",
        ],
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "p0_baseline": p0_baseline,
        "p1_baseline": p1_baseline,
        "p2_atomics_total": P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "counts": counts,
        "defects_remaining": defects,
        "external_runtime_gates": external_gates,
        "runtime_proofs": {
            "p2_pytest": p2_pytest,
            "p1_regression_pytest": p1_regression,
            "postgres_p2_spine": postgres_p2,
        },
        "prior_batch_evidence": ["TEMPORAL_P2_COMPLETE_AND_CLOSURE_EVIDENCE.json"],
        "reconciliation": reconciliation,
        "final_verdict": verdict,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPO / "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "PHASE": "P2_OUTCOME_AND_EVIDENCE",
                "TOTAL_ATOMICS": P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
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
    return 0 if verdict == "PHASE_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
