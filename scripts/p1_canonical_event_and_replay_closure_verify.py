#!/usr/bin/env python3
"""P1_CANONICAL_EVENT_AND_REPLAY closure — authoritative 31-atomic reconciliation."""

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
ARTIFACT = Path("/opt/cursor/artifacts/TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json")
RTM_PATH = REPO / "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json"
P0_EVIDENCE = REPO / "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json"

EVIDENCE_BY_ATOMIC: dict[str, dict[str, str]] = {
    "TEMP-AR-0044": {
        "evidence": "tests/test_temporal_p1_closure_runtime_e2e.py::test_temp_ar_0044_canonical_store_is_not_unstructured_file_archive",
        "tests": "SECURITY_TEST",
    },
    "TEMP-AR-0045": {
        "evidence": "tests/test_temporal_p1_closure_runtime_e2e.py::test_temp_ar_0045_canonical_ingestion_path_modules_present + normalization.py",
        "tests": "STATIC_INSPECTION",
    },
    "TEMP-AR-0046": {
        "evidence": "tests/test_temporal_p1_1_canonical_event_store.py lineage + revision preservation",
        "tests": "PROVENANCE_CHECK",
    },
    "TEMP-AR-0047": {
        "evidence": "tests/test_temporal_p1_1_canonical_event_store.py provenance/source identity",
        "tests": "UNIT_TEST",
    },
    "TEMP-AR-0048": {
        "evidence": "tests/test_temporal_p1_1_canonical_event_store.py source_version/dataset_version metadata",
        "tests": "UNIT_TEST",
    },
    "TEMP-AR-0049": {
        "evidence": "tests/test_temporal_p1_closure_runtime_e2e.py dedup tests + production_spine idempotency",
        "tests": "UNIT_TEST",
    },
    "TEMP-AR-0050": {
        "evidence": "tests/test_temporal_p1_1_canonical_event_store.py revision/amendment lineage",
        "tests": "UNIT_TEST",
    },
    "TEMP-AR-0051": {
        "evidence": "tests/test_temporal_p1_1_canonical_event_store.py conflict preservation",
        "tests": "UNIT_TEST",
    },
    "TEMP-AR-0052": {
        "evidence": "tests/test_temporal_p1_1_canonical_event_store.py deterministic retrieval + P0 reconstruction",
        "tests": "UNIT_TEST",
    },
    "TEMP-AR-0053": {
        "evidence": "tests/test_temporal_p1_1_canonical_event_store.py rights/provenance metadata",
        "tests": "PROVENANCE_CHECK",
    },
    "TEMP-AR-0054": {
        "evidence": "tests/test_temporal_p1_closure_runtime_e2e.py::test_temp_ar_0054_retention_policy_reference_and_descriptor",
        "tests": "UNIT_TEST",
    },
    "TEMP-AR-0055": {
        "evidence": "tests/test_temporal_p1_1_canonical_event_store.py + replay manifest lineage fields",
        "tests": "PROVENANCE_CHECK",
    },
    "TEMP-AR-0056": {
        "evidence": "tests/test_temporal_p1_closure_runtime_e2e.py::test_temp_ar_0056_raw_not_discarded_for_low_learning_priority",
        "tests": "SECURITY_TEST",
    },
    "TEMP-AR-0057": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py full decision path stages",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0058": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py multi_scenario assets dimension",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0059": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py multi_scenario venues dimension",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0060": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py multi_scenario time_horizons dimension",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0061": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py multi_scenario historical_periods dimension",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0062": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py multi_scenario regimes dimension",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0063": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py multi_scenario model_versions dimension",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0064": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py multi_scenario thresholds dimension",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0065": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py multi_scenario source_availability dimension",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0066": {
        "evidence": "tests/test_temporal_p1_2_deterministic_mass_replay.py reproducibility fingerprint",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0067": {
        "evidence": "tests/test_temporal_p1_2_deterministic_mass_replay.py PIT correctness + lookahead rejection",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0068": {
        "evidence": "tests/test_temporal_p1_2_deterministic_mass_replay.py provenance-bound manifest",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0069": {
        "evidence": "tests/test_temporal_p1_2_deterministic_mass_replay.py version-bound dataset context",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0070": {
        "evidence": "tests/test_temporal_p1_2_deterministic_mass_replay.py deterministic ordering + fingerprint stability",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0071": {
        "evidence": "tests/test_temporal_p1_3_remaining_replay_coverage.py compare_replay_runs across model versions",
        "tests": "REPLAY_TEST",
    },
    "TEMP-AR-0072": {
        "evidence": "tests/test_temporal_p1_closure_runtime_e2e.py::test_temp_ar_0072_replay_evidence_class_not_live_forward_proof",
        "tests": "PERFORMANCE_TEST",
    },
    "TEMP-AR-0377": {
        "evidence": "blackdark/temporal/event_store.py + PostgresEventStore in persistence/postgres.py established",
        "tests": "STATIC_INSPECTION",
    },
    "TEMP-AR-0380": {
        "evidence": "blackdark/temporal/replay.py run_deterministic_mass_replay + spine replay stage wiring",
        "tests": "STATIC_INSPECTION",
    },
}

P1_TEST_FILES = (
    "tests/test_temporal_p1_1_canonical_event_store.py",
    "tests/test_temporal_p1_2_deterministic_mass_replay.py",
    "tests/test_temporal_p1_3_remaining_replay_coverage.py",
    "tests/test_temporal_p1_closure_runtime_e2e.py",
)


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


async def _verify_postgres_replay_round_trip() -> dict[str, Any]:
    import asyncpg

    from blackdark.data.db import get_session, get_session_factory
    from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
    from blackdark.temporal.persistence.postgres import PostgresEventStore
    from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine
    from blackdark.temporal.replay import ReplayRequest, run_deterministic_mass_replay

    import config
    import blackdark.data.db as db_module

    config.DATABASE_URL = POSTGRES
    db_module._engine = None
    db_module._session_factory = None
    if not db_module._schema_ready:
        from blackdark.data.db import init_data_engine

        await init_data_engine()

    suffix = uuid.uuid4().hex[:8]
    sim = "2026-05-01T02:00:00Z"
    avail = "2026-05-01T01:00:00Z"
    sim_dt = datetime.fromisoformat("2026-05-01T02:00:00+00:00")
    idem = f"p1-closure-{suffix}"
    payload = {
        "entity_key": f"P1CLOSE-{suffix}",
        "event_type": "market_tick",
        "payload": {"proof": suffix},
        "observation": build_observation_dict(
            event_time=sim,
            observed_time=sim,
            available_at=avail,
            ingested_at=avail,
            effective_at=sim,
            revised_at=avail,
        ),
        "provenance": build_provenance_dict(
            source="p1-closure",
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
                subject_identity=f"P1CLOSE-{suffix}",
                input_identity=f"input-{suffix}",
                idempotency_key=idem,
            ),
        )
    assert spine.event_id

    db_module._engine = None
    db_module._session_factory = None
    get_session_factory()

    async with get_session() as session:
        store = PostgresEventStore(session)
        await store.hydrate()
        replay = run_deterministic_mass_replay(
            ReplayRequest(
                event_source=store,
                start_time=sim_dt,
                end_time=sim_dt,
                replay_clock_or_schedule=(sim_dt,),
                strict_mode=True,
                replay_parameters={"model_version": "model-v1"},
                dataset_or_source_version_context={"dataset_version": f"ds-close-{suffix}"},
            )
        )

    raw = await asyncpg.connect(POSTGRES)
    row = await raw.fetchrow(
        "SELECT event_id, idempotency_key FROM te_canonical_events WHERE event_id=$1",
        spine.event_id,
    )
    await raw.close()
    return {
        "event_id": spine.event_id,
        "idempotency_key": idem,
        "postgres_row_present": row is not None,
        "hydrated_event_count": store.event_count,
        "replay_id": replay.replay_id,
        "determinism_fingerprint": replay.determinism_fingerprint,
        "evidence_class": replay.evidence_class,
        "replay_manifest_complete": bool(replay.replay_manifest),
        "spine_replay_stage_completed": any(
            s.get("stage") == "replay" and s.get("status") == "completed"
            for s in spine.observability.get("stages", [])
        ),
    }


def _p0_baseline_closed() -> dict[str, Any]:
    if not P0_EVIDENCE.exists():
        return {"closed": False, "reason": "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json missing"}
    data = json.loads(P0_EVIDENCE.read_text(encoding="utf-8"))
    return {
        "closed": data.get("final_verdict") == "P0_CLOSED",
        "final_verdict": data.get("final_verdict"),
        "verified": data.get("counts", {}).get("VERIFIED"),
    }


async def main() -> int:
    with RTM_PATH.open(encoding="utf-8") as handle:
        rtm = json.load(handle)

    p1_rows = [row for row in rtm["rtm_rows"] if row["phase_allocation"] == "P1_CANONICAL_EVENT_AND_REPLAY"]
    if len(p1_rows) != 31:
        raise SystemExit(f"Expected 31 P1 atomics, found {len(p1_rows)}")

    p0_baseline = _p0_baseline_closed()
    p1_pytest = _run_pytest(P1_TEST_FILES)
    p0_regression = _run_pytest(
        (
            "tests/test_temporal_p0_1_truth_primitive.py",
            "tests/test_temporal_p0_2_pit_reconstruction.py",
            "tests/test_temporal_p0_3_leakage_firewall.py",
        )
    )

    postgres_replay: dict[str, Any]
    try:
        postgres_replay = await _verify_postgres_replay_round_trip()
        postgres_ok = (
            postgres_replay["postgres_row_present"]
            and postgres_replay["replay_manifest_complete"]
            and postgres_replay["spine_replay_stage_completed"]
        )
    except Exception as exc:
        postgres_replay = {"error": str(exc), "status": "FAILED"}
        postgres_ok = False

    reconciliation: list[dict[str, Any]] = []
    counts = {
        "VERIFIED": 0,
        "IMPLEMENTED_NOT_VERIFIED": 0,
        "NOT_IMPLEMENTED": 0,
        "EXTERNAL_RUNTIME_PENDING": 0,
    }

    for row in sorted(p1_rows, key=lambda item: item["atomic_requirement_id"]):
        aid = row["atomic_requirement_id"]
        evidence = EVIDENCE_BY_ATOMIC.get(aid, {})
        status = "VERIFIED"

        if not evidence:
            status = "NOT_IMPLEMENTED"
        elif not p1_pytest["passed"]:
            status = "IMPLEMENTED_NOT_VERIFIED"
        elif aid in {"TEMP-AR-0377", "TEMP-AR-0380"} and not postgres_ok:
            status = "IMPLEMENTED_NOT_VERIFIED"

        counts[status] += 1
        reconciliation.append(
            {
                "atomic_requirement_id": aid,
                "parent_primary_requirement_id": row["parent_primary_requirement_id"],
                "phase_allocation": row["phase_allocation"],
                "verification_method": row["verification_method"],
                "atomic_obligation": row["atomic_obligation"],
                "status": status,
                "evidence": evidence.get("evidence"),
                "evidence_tests": evidence.get("tests"),
            }
        )

    defects: list[str] = []
    if not p0_baseline.get("closed"):
        defects.append("P0 baseline not closed — regression guard failed")
    if not p1_pytest["passed"]:
        defects.append("P1 focused pytest suite failed")
    if not p0_regression["passed"]:
        defects.append("P0 regression pytest failed")
    if not postgres_ok:
        defects.append("Postgres hydrate/replay round-trip not verified")

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
        "scope": "P1_CANONICAL_EVENT_AND_REPLAY",
        "governing_sources": [
            "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md",
            "TEMPORAL_PRIMARY_REQUIREMENTS.json",
            "TEMPORAL_ATOMIC_REQUIREMENTS.json",
            "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json",
            "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json",
        ],
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "p0_baseline": p0_baseline,
        "p1_atomics_total": 31,
        "counts": counts,
        "defects_remaining": defects,
        "external_runtime_gates": external_gates,
        "runtime_proofs": {
            "p1_pytest": p1_pytest,
            "p0_regression_pytest": p0_regression,
            "postgres_replay_round_trip": postgres_replay,
        },
        "prior_batch_evidence": [
            "TEMPORAL_P1_1_CANONICAL_EVENT_STORE_EVIDENCE.json",
            "TEMPORAL_P1_2_DETERMINISTIC_MASS_REPLAY_EVIDENCE.json",
            "TEMPORAL_P1_3_REMAINING_REPLAY_COVERAGE_EVIDENCE.json",
        ],
        "reconciliation": reconciliation,
        "final_verdict": verdict,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPO / "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "PHASE": "P1_CANONICAL_EVENT_AND_REPLAY",
                "TOTAL_ATOMICS": 31,
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
