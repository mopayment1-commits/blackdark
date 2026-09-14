#!/usr/bin/env python3
"""P3_SHADOW_AND_REGIME closure — authoritative 63-atomic reconciliation."""

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
ARTIFACT = Path("/opt/cursor/artifacts/TEMPORAL_P3_SHADOW_AND_REGIME_CLOSURE_EVIDENCE.json")
RTM_PATH = REPO / "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json"
P0_EVIDENCE = REPO / "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json"
P1_EVIDENCE = REPO / "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json"
P2_EVIDENCE = REPO / "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json"

from blackdark.temporal.p3_closure_verification import (
    evaluate_p3_closure_assertions,
    probe_temp_ar_0164_status,
)
from blackdark.temporal.p3_requirement_registry import (
    P3_ATOMIC_REQUIREMENT_IDS,
    P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
)

OWNER_BASE_EVIDENCE: dict[str, str] = {
    "FORWARD_SHADOW": "tests/test_temporal_p3_shadow_and_regime.py forward shadow tests",
    "REGIME_INTELLIGENCE": "tests/test_temporal_p3_shadow_and_regime.py regime intelligence tests",
    "FAILURE_SURPRISE_ABSTENTION": "tests/test_temporal_p3_failure_surprise_abstention.py corpus tests",
    "CROSS_CUTTING_GOVERNANCE": "tests/test_temporal_p3_closure.py closure probe tests",
}

RUNTIME_EVIDENCE_OVERRIDES: dict[str, str] = {
    "TEMP-AR-0124": "tests/test_temporal_p3_closure_runtime_e2e.py::test_temp_ar_0124_pre_outcome_receipt_spine_integration",
    "TEMP-AR-0164": "blackdark/temporal/reality_anchor.py + probe_temp_ar_0164_status (external gate)",
    "TEMP-AR-0167": "tests/test_temporal_p3_closure_runtime_e2e.py::test_temp_ar_0167_failure_surprise_corpus_integration",
    "TEMP-AR-0183": "tests/test_temporal_p3_shadow_and_regime.py replay evidence separation tests",
}

P3_TEST_FILES = (
    "tests/test_temporal_p3_shadow_and_regime.py",
    "tests/test_temporal_p3_failure_surprise_abstention.py",
    "tests/test_temporal_p3_post_outcome_shadow_guard.py",
    "tests/test_temporal_p3_closure.py",
    "tests/test_temporal_p3_closure_runtime_e2e.py",
)


def _build_evidence_by_atomic(rtm_rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for aid in P3_ATOMIC_REQUIREMENT_IDS:
        row = rtm_rows[aid]
        owner = row.get("logical_owner") or "CROSS_CUTTING_GOVERNANCE"
        evidence[aid] = {
            "evidence": RUNTIME_EVIDENCE_OVERRIDES.get(aid, OWNER_BASE_EVIDENCE.get(owner, "p3_closure_verification probes")),
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


async def _verify_postgres_p3_spine() -> dict[str, Any]:
    from blackdark.data.db import get_session, get_session_factory
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
    sim = "2026-09-01T02:00:00Z"
    avail = "2026-09-01T01:00:00Z"
    sim_dt = datetime.fromisoformat("2026-09-01T02:00:00+00:00")
    idem = f"p3-closure-{suffix}"
    payload = {
        "entity_key": f"P3CLOSE-{suffix}",
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
            source="p3-closure",
            source_version="v1",
            dataset_version=f"ds-close-{suffix}",
            rights_or_provenance={"permitted_purpose": "forward_shadow"},
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
                subject_identity=f"P3CLOSE-{suffix}",
                input_identity=f"input-{suffix}",
                idempotency_key=idem,
            ),
        )
    assert spine.receipt_id

    db_module._engine = None
    db_module._session_factory = None
    get_session_factory()

    import asyncpg

    raw = await asyncpg.connect(POSTGRES)
    row = await raw.fetchrow(
        "SELECT receipt_id, evidence_class, receipt_payload FROM te_forward_shadow_receipts WHERE receipt_id=$1",
        spine.receipt_id,
    )
    await raw.close()
    payload_status = None
    if row:
        payload = row["receipt_payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        payload_status = payload.get("status")

    return {
        "receipt_id": spine.receipt_id,
        "p3_metadata_present": spine.p3_metadata is not None,
        "evidence_class": row["evidence_class"] if row else None,
        "receipt_status": payload_status,
        "p3_pipeline_stage_completed": any(
            s.get("stage") == "p3_pipeline" and s.get("status") == "completed"
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

    p3_rows = [row for row in rtm["rtm_rows"] if row["phase_allocation"] == "P3_SHADOW_AND_REGIME"]
    if len(p3_rows) != P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS:
        raise SystemExit(
            f"Expected {P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS} P3 atomics, found {len(p3_rows)}"
        )
    if set(P3_ATOMIC_REQUIREMENT_IDS) != {row["atomic_requirement_id"] for row in p3_rows}:
        raise SystemExit("P3 registry IDs do not match RTM phase allocation")

    rtm_by_id = {row["atomic_requirement_id"]: row for row in p3_rows}
    evidence_by_atomic = _build_evidence_by_atomic(rtm_by_id)

    p0_baseline = _baseline_closed(P0_EVIDENCE, "P0_CLOSED")
    p1_baseline = _baseline_closed(P1_EVIDENCE, "PHASE_CLOSED")
    p2_baseline = _baseline_closed(P2_EVIDENCE, "PHASE_CLOSED")
    p3_pytest = _run_pytest(P3_TEST_FILES)
    p2_regression = _run_pytest(
        (
            "tests/test_temporal_p2_outcome_and_evidence.py",
            "tests/test_temporal_p2_closure_runtime_e2e.py",
        )
    )
    closure_probes = evaluate_p3_closure_assertions()
    temp_ar_0164 = probe_temp_ar_0164_status()

    postgres_p3: dict[str, Any]
    try:
        postgres_p3 = await _verify_postgres_p3_spine()
        postgres_ok = (
            postgres_p3.get("p3_metadata_present")
            and postgres_p3.get("p3_pipeline_stage_completed")
            and postgres_p3.get("evidence_class") == "FORWARD_SHADOW"
            and postgres_p3.get("receipt_status") == "pre_outcome"
        )
    except Exception as exc:
        postgres_p3 = {"error": str(exc), "status": "FAILED"}
        postgres_ok = False

    reconciliation: list[dict[str, Any]] = []
    counts = {
        "VERIFIED": 0,
        "IMPLEMENTED_NOT_VERIFIED": 0,
        "NOT_IMPLEMENTED": 0,
        "EXTERNAL_RUNTIME_PENDING": 0,
    }

    external_gates: dict[str, Any] = {}

    for aid in sorted(P3_ATOMIC_REQUIREMENT_IDS):
        row = rtm_by_id[aid]
        evidence = evidence_by_atomic[aid]
        status = "VERIFIED"

        if aid in P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS:
            if temp_ar_0164.get("external_evidence_pending") and not temp_ar_0164.get("forward_time_passage_verified"):
                status = "EXTERNAL_RUNTIME_PENDING"
                external_gates[aid] = {
                    "reason": "requires real forward time passage between receipt issuance and outcome evaluation",
                    "local_engineering_complete": temp_ar_0164.get("local_engineering_complete"),
                    "forward_time_passage_verified": temp_ar_0164.get("forward_time_passage_verified"),
                }
            elif not temp_ar_0164.get("local_engineering_complete"):
                status = "IMPLEMENTED_NOT_VERIFIED"
        elif not evidence:
            status = "NOT_IMPLEMENTED"
        elif not p3_pytest["passed"]:
            status = "IMPLEMENTED_NOT_VERIFIED"
        elif aid == "TEMP-AR-0124" and not postgres_ok:
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
    if not p3_pytest["passed"]:
        defects.append("P3 focused pytest suite failed")
    if not p2_regression["passed"]:
        defects.append("P2 regression pytest failed")
    if not closure_probes["closure_assertions"].get("P3_CLOSED"):
        defects.append("P3 closure runtime probes failed")
    if not postgres_ok:
        defects.append("Postgres P3 spine/receipt round-trip not verified")

    if counts["NOT_IMPLEMENTED"] or counts["IMPLEMENTED_NOT_VERIFIED"] or defects:
        verdict = "PHASE_NOT_CLOSED"
    elif counts["EXTERNAL_RUNTIME_PENDING"]:
        verdict = "PHASE_CLOSED_WITH_EXTERNAL_RUNTIME_GATE"
    else:
        verdict = "PHASE_CLOSED"

    report = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "scope": "P3_SHADOW_AND_REGIME",
        "governing_sources": [
            "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md",
            "TEMPORAL_PRIMARY_REQUIREMENTS.json",
            "TEMPORAL_ATOMIC_REQUIREMENTS.json",
            "TEMPORAL_REQUIREMENTS_TRACEABILITY_MATRIX.json",
            "TEMPORAL_P0_FOUNDATION_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P1_CANONICAL_EVENT_AND_REPLAY_CLOSURE_EVIDENCE.json",
            "TEMPORAL_P2_OUTCOME_AND_EVIDENCE_CLOSURE_EVIDENCE.json",
        ],
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "p0_baseline": p0_baseline,
        "p1_baseline": p1_baseline,
        "p2_baseline": p2_baseline,
        "p3_atomics_total": P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "counts": counts,
        "defects_remaining": defects,
        "external_runtime_gates": external_gates,
        "runtime_proofs": {
            "p3_pytest": p3_pytest,
            "p2_regression_pytest": p2_regression,
            "closure_probes": closure_probes,
            "temp_ar_0164": temp_ar_0164,
            "postgres_p3_spine": postgres_p3,
        },
        "prior_batch_evidence": ["TEMPORAL_P3_COMPLETE_AND_CLOSURE_EVIDENCE.json"],
        "reconciliation": reconciliation,
        "final_verdict": verdict,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPO / "TEMPORAL_P3_SHADOW_AND_REGIME_CLOSURE_EVIDENCE.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "PHASE": "P3_SHADOW_AND_REGIME",
                "TOTAL_ATOMICS": P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
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
