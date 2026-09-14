#!/usr/bin/env python3
"""P0 runtime/deployment verification harness — evidence only, no code changes."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

POSTGRES_URL = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "test-admin-key-please-rotate")

TE_TABLES = (
    "te_canonical_events",
    "te_evidence_records",
    "te_forward_shadow_receipts",
    "te_forward_shadow_corrections",
    "te_contamination_registry",
    "te_walk_forward_runs",
    "te_reality_anchor_observations",
    "te_spine_runs",
)

TE_INDEXES = (
    "idx_te_canonical_events_entity",
    "idx_te_canonical_events_type",
    "idx_te_evidence_records_class",
    "idx_te_forward_shadow_subject",
    "idx_te_contamination_dataset",
    "idx_te_walk_forward_dataset",
    "idx_te_reality_anchor_anchor",
    "idx_te_spine_runs_stage",
)


def _observation(sim: str, avail: str) -> dict:
    from blackdark.temporal.normalization import build_observation_dict

    return build_observation_dict(
        event_time=sim,
        observed_time=sim,
        available_at=avail,
        ingested_at=avail,
        effective_at=sim,
        revised_at=avail,
    )


def _provenance() -> dict:
    from blackdark.temporal.normalization import build_provenance_dict

    return build_provenance_dict(
        source="binance",
        source_version="v1",
        dataset_version="ds-runtime-1",
        rights_or_provenance={"permitted_purpose": "historical_evaluation"},
    )


async def verify_migrations(report: dict[str, Any]) -> None:
    import asyncpg

    import config
    import blackdark.data.db as db_module
    from blackdark.data.db import init_data_engine
    from blackdark.data.migrate import apply_migrations

    config.DATABASE_URL = POSTGRES_URL
    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False

    raw = await asyncpg.connect(POSTGRES_URL)
    await raw.execute("DROP SCHEMA IF EXISTS public CASCADE")
    await raw.execute("CREATE SCHEMA public")
    await raw.close()

    result = await apply_migrations()
    report["migration"] = {
        "applied_count": len(result["applied"]),
        "skipped_count": len(result["skipped"]),
        "total_migrations": result["total"],
        "018_in_applied": "018_temporal_spine" in result["applied"],
        "applied_tail": result["applied"][-5:],
    }

    raw = await asyncpg.connect(POSTGRES_URL)
    tables = await raw.fetch(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_name LIKE 'te_%'
        ORDER BY table_name
        """
    )
    found_tables = [r["table_name"] for r in tables]
    report["migration"]["te_tables_found"] = found_tables
    report["migration"]["te_tables_missing"] = [t for t in TE_TABLES if t not in found_tables]

    indexes = await raw.fetch(
        """
        SELECT indexname FROM pg_indexes
        WHERE schemaname='public' AND indexname LIKE 'idx_te_%'
        ORDER BY indexname
        """
    )
    found_idx = [r["indexname"] for r in indexes]
    report["migration"]["indexes_found"] = found_idx
    report["migration"]["indexes_missing"] = [i for i in TE_INDEXES if i not in found_idx]

    versions = await raw.fetch("SELECT version FROM data_engine_migrations ORDER BY version")
    report["migration"]["migration_versions"] = [r["version"] for r in versions]
    report["migration"]["018_in_ledger"] = any(v["version"] == "018_temporal_spine" for v in versions)

    # rollback semantics: failed insert should not persist partial spine row
    try:
        await raw.execute(
            """
            INSERT INTO te_canonical_events (
                event_id, entity_key, event_type, payload, observation, provenance,
                record_version
            ) VALUES (
                'rollback-test', 'X', 't', '{}', '{}', '{}', '1'
            )
            """
        )
        await raw.execute("INSERT INTO te_canonical_events (event_id) VALUES ('bad')")
    except Exception:
        pass
    count = await raw.fetchval("SELECT COUNT(*) FROM te_canonical_events WHERE event_id='rollback-test'")
    report["migration"]["rollback_partial_write_prevented"] = count == 0
    await raw.execute("DELETE FROM te_canonical_events WHERE event_id='rollback-test'")
    await raw.close()

    await init_data_engine()


def verify_api_runtime(report: dict[str, Any]) -> None:
    os.environ["DATABASE_URL"] = POSTGRES_URL
    os.environ["ADMIN_API_KEY"] = ADMIN_KEY
    os.environ["ADMIN_MFA_REQUIRED"] = "false"
    os.environ["ENV"] = "development"

    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    headers = {"X-Admin-Key": ADMIN_KEY}

    sim = "2026-01-15T10:00:00Z"
    avail = "2026-01-15T09:00:00Z"
    ingest_body = {
        "entity_key": "BTCUSDT",
        "event_type": "market_tick",
        "payload": {"price": "42000.0"},
        "observation": _observation(sim, avail),
        "provenance": _provenance(),
        "simulated_time": sim,
        "prediction": {"direction": "buy"},
        "confidence": 0.81,
        "abstention_state": "act",
        "subject_identity": "BTCUSDT",
        "input_identity": "runtime-ingest-1",
        "idempotency_key": "runtime-verify-ingest-1",
    }

    t0 = time.perf_counter()
    resp = client.post(
        "/api/temporal/spine/ingest",
        json=ingest_body,
        headers={**headers, "Idempotency-Key": "runtime-verify-ingest-1"},
    )
    ingest_ms = (time.perf_counter() - t0) * 1000
    report["api"]["spine_ingest"] = {
        "status_code": resp.status_code,
        "latency_ms": round(ingest_ms, 2),
        "body": resp.json() if resp.status_code < 500 else resp.text[:500],
    }

    pred_body = {
        "symbol": "ETHUSDT",
        "direction": "buy",
        "model_version": "runtime-model-v1",
        "payload": {
            "temporal": {
                "observation": _observation("2026-01-15T11:00:00Z", "2026-01-15T10:30:00Z"),
                "provenance": _provenance(),
                "simulated_time": "2026-01-15T11:00:00Z",
                "confidence": 0.66,
                "abstention_state": "act",
            }
        },
    }
    t1 = time.perf_counter()
    pred_resp = client.post(
        "/api/v1/data/predictions",
        json=pred_body,
        headers={"Idempotency-Key": "runtime-verify-pred-1"},
    )
    pred_ms = (time.perf_counter() - t1) * 1000
    report["api"]["predictions"] = {
        "status_code": pred_resp.status_code,
        "latency_ms": round(pred_ms, 2),
        "body": pred_resp.json() if pred_resp.status_code < 500 else pred_resp.text[:500],
    }

    health = client.get("/api/temporal/health")
    report["api"]["health"] = {"status_code": health.status_code, "body": health.json()}


async def verify_db_rows(report: dict[str, Any]) -> None:
    import asyncpg

    raw = await asyncpg.connect(POSTGRES_URL)
    events = await raw.fetchval("SELECT COUNT(*) FROM te_canonical_events")
    evidence = await raw.fetchval("SELECT COUNT(*) FROM te_evidence_records")
    receipts = await raw.fetchval("SELECT COUNT(*) FROM te_forward_shadow_receipts")
    anchors = await raw.fetch("SELECT * FROM te_reality_anchor_observations ORDER BY observed_at DESC LIMIT 5")
    spine_runs = await raw.fetchval("SELECT COUNT(*) FROM te_spine_runs")
    sample_event = await raw.fetchrow(
        "SELECT event_id, entity_key, provenance, observation FROM te_canonical_events ORDER BY created_at DESC LIMIT 1"
    )
    report["db"] = {
        "canonical_events": events,
        "evidence_records": evidence,
        "forward_shadow_receipts": receipts,
        "reality_anchor_observations": len(anchors),
        "spine_runs": spine_runs,
        "latest_event_id": sample_event["event_id"] if sample_event else None,
        "latest_provenance": json.loads(sample_event["provenance"]) if sample_event else None,
    }
    if anchors:
        a = anchors[0]
        report["reality_anchor"] = {
            "observation_id": a["observation_id"],
            "forward_time_passage_verified": a["forward_time_passage_verified"],
            "external_evidence_pending": a["external_evidence_pending"],
            "external_gate_requirement_id": a["external_gate_requirement_id"],
            "simulated_time_used": a["simulated_time_used"],
            "observed_at": a["observed_at"].isoformat(),
            "payload": json.loads(a["observation_payload"]),
        }
    await raw.close()


async def verify_restart_persistence(report: dict[str, Any], event_id: str | None) -> None:
    import blackdark.data.db as db_module
    from blackdark.data.db import get_session, init_data_engine
    from blackdark.data.temporal_repository import get_canonical_event, get_evidence_record

    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False
    await init_data_engine()

    if not event_id:
        report["restart"] = {"skipped": True, "reason": "no event_id"}
        return

    async with get_session() as session:
        event = await get_canonical_event(session, event_id)
    report["restart"] = {
        "event_survives": event is not None,
        "event_id": event_id,
        "entity_key": event.get("entity_key") if event else None,
        "provenance_source": (json.loads(event["provenance"]) if event else {}).get("source"),
    }


def verify_failure_paths(report: dict[str, Any]) -> None:
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    headers = {"X-Admin-Key": ADMIN_KEY}
    cases: list[dict[str, Any]] = []

    def record(name: str, status: int, expected_fail: bool, detail: Any) -> None:
        cases.append(
            {
                "case": name,
                "status_code": status,
                "expected_fail_closed": expected_fail,
                "pass": (status >= 400) if expected_fail else (200 <= status < 300),
                "detail": detail,
            }
        )

    # missing provenance
    bad_prov = {
        "entity_key": "BTCUSDT",
        "event_type": "market_tick",
        "observation": _observation("2026-01-15T10:00:00Z", "2026-01-15T09:00:00Z"),
        "provenance": {"source": "binance"},
        "simulated_time": "2026-01-15T10:00:00Z",
        "prediction": {"direction": "buy"},
        "confidence": 0.5,
        "abstention_state": "act",
        "subject_identity": "BTCUSDT",
        "input_identity": "fail-prov",
    }
    r = client.post("/api/temporal/spine/ingest", json=bad_prov, headers=headers)
    record("missing_provenance", r.status_code, True, r.json() if r.status_code < 500 else r.text[:200])

    # PIT violation: available_at after simulated_time
    pit_bad = {
        "entity_key": "BTCUSDT",
        "event_type": "market_tick",
        "observation": _observation("2026-01-15T10:00:00Z", "2026-01-15T11:00:00Z"),
        "provenance": _provenance(),
        "simulated_time": "2026-01-15T10:00:00Z",
        "prediction": {"direction": "buy"},
        "confidence": 0.5,
        "abstention_state": "act",
        "subject_identity": "BTCUSDT",
        "input_identity": "fail-pit",
    }
    r = client.post("/api/temporal/spine/ingest", json=pit_bad, headers=headers)
    record("pit_violation", r.status_code, True, r.json() if r.status_code < 500 else r.text[:200])

    # idempotent duplicate
    dup_headers = {**headers, "Idempotency-Key": "runtime-verify-ingest-1"}
    good = {
        "entity_key": "BTCUSDT",
        "event_type": "market_tick",
        "observation": _observation("2026-01-15T10:00:00Z", "2026-01-15T09:00:00Z"),
        "provenance": _provenance(),
        "simulated_time": "2026-01-15T10:00:00Z",
        "prediction": {"direction": "buy"},
        "confidence": 0.5,
        "abstention_state": "act",
        "subject_identity": "BTCUSDT",
        "input_identity": "dup",
    }
    r1 = client.post("/api/temporal/spine/ingest", json=good, headers=dup_headers)
    r2 = client.post("/api/temporal/spine/ingest", json=good, headers=dup_headers)
    record(
        "idempotent_duplicate",
        r2.status_code,
        False,
        {
            "first_event": r1.json().get("event_id") if r1.status_code < 300 else None,
            "second_event": r2.json().get("event_id") if r2.status_code < 300 else None,
            "same_event_id": (
                r1.json().get("event_id") == r2.json().get("event_id")
                if r1.status_code < 300 and r2.status_code < 300
                else None
            ),
        },
    )

    # contamination via walk-forward API
    wf = {
        "dataset_id": "ds-runtime-1",
        "samples": [{"event_time": "2026-01-15T00:30:00Z", "value": 1}],
        "series_start": "2026-01-15T00:00:00Z",
        "series_end": "2026-01-15T08:00:00Z",
        "train_duration_seconds": 7200,
        "eval_duration_seconds": 3600,
        "step_seconds": 3600,
    }
    r = client.post("/api/temporal/walk-forward/evaluate", json=wf, headers=headers)
    record("walk_forward_smoke", r.status_code, False, {"fold_count": r.json().get("fold_count") if r.status_code < 300 else r.text[:120]})

    report["failure_paths"] = cases


def verify_load_smoke(report: dict[str, Any]) -> None:
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    headers = {"X-Admin-Key": ADMIN_KEY}
    n = 10
    latencies: list[float] = []
    errors = 0
    event_ids: list[str | None] = []

    def one(i: int) -> tuple[int, float, str | None]:
        body = {
            "entity_key": f"LOAD{i}",
            "event_type": "market_tick",
            "observation": _observation("2026-01-15T10:00:00Z", "2026-01-15T09:00:00Z"),
            "provenance": _provenance(),
            "simulated_time": "2026-01-15T10:00:00Z",
            "prediction": {"direction": "buy"},
            "confidence": 0.5,
            "abstention_state": "act",
            "subject_identity": f"LOAD{i}",
            "input_identity": f"load-{i}",
        }
        t0 = time.perf_counter()
        r = client.post(
            "/api/temporal/spine/ingest",
            json=body,
            headers={**headers, "Idempotency-Key": f"load-smoke-{i}"},
        )
        ms = (time.perf_counter() - t0) * 1000
        eid = r.json().get("event_id") if r.status_code < 300 else None
        return r.status_code, ms, eid

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(one, i) for i in range(n)]
        for fut in as_completed(futures):
            status, ms, eid = fut.result()
            latencies.append(ms)
            event_ids.append(eid)
            if status >= 400:
                errors += 1

    report["load_smoke"] = {
        "requests": n,
        "errors": errors,
        "success_rate": round((n - errors) / n, 3),
        "latency_ms_min": round(min(latencies), 2),
        "latency_ms_max": round(max(latencies), 2),
        "latency_ms_avg": round(sum(latencies) / len(latencies), 2),
        "unique_event_ids": len({e for e in event_ids if e}),
    }


def verify_live_feed_compatibility(report: dict[str, Any]) -> None:
    report["live_feed"] = {
        "existing_ingestors": [
            "blackdark/data/ingestors/binance.py:ingest_ohlcv",
            "blackdark/data/ingestors/coingecko.py:ingest_ohlcv",
            "blackdark/data/ingestors/kraken.py:ingest_ohlcv",
        ],
        "temporal_spine_hook_present": False,
        "status": "LIVE_FEED_EVIDENCE_PENDING",
        "reason": "Existing Wave01 ingestors write to ohlcv_data/data_provenance; no production hook maps live ingest rows into run_production_temporal_spine without new integration work.",
    }


async def main() -> int:
    report: dict[str, Any] = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "environment": {
            "host": socket.gethostname(),
            "postgres_url": POSTGRES_URL.split("@")[-1],
            "mode": "local_postgres_staging_compatible",
            "branch": os.popen("git branch --show-current").read().strip(),
        },
        "api": {},
        "migration": {},
        "db": {},
        "reality_anchor": {},
        "failure_paths": [],
        "load_smoke": {},
        "live_feed": {},
        "restart": {},
    }

    if not _postgres_reachable():
        print(json.dumps({"error": "postgres_unreachable"}, indent=2))
        return 1

    await verify_migrations(report)
    verify_api_runtime(report)
    await verify_db_rows(report)
    event_id = report.get("api", {}).get("spine_ingest", {}).get("body", {}).get("event_id")
    await verify_restart_persistence(report, event_id)
    verify_failure_paths(report)
    verify_load_smoke(report)
    verify_live_feed_compatibility(report)

    out = Path("/opt/cursor/artifacts/p0_runtime_verification_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    return 0


def _postgres_reachable() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=2):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
