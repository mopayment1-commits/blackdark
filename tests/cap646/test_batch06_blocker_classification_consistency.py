"""Machine-readable consistency tests for Batch06 blocker classification taxonomy."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> dict:
    return json.loads((ROOT / "docs" / name).read_text(encoding="utf-8"))


def test_status_queues_four_taxonomy():
    queues = _load("BATCH06_STATUS_QUEUES.json")
    assert "QUEUE_A_LOCAL_COMPLETE" in queues
    assert "QUEUE_B_RAILWAY_ONLY" in queues
    assert "QUEUE_C_INDEPENDENT_REVIEW_ONLY" in queues
    assert "QUEUE_D_RAILWAY_THEN_INDEPENDENT_REVIEW" in queues
    assert queues["QUEUE_C_INDEPENDENT_REVIEW_ONLY"]["count"] == 0
    assert queues["QUEUE_D_RAILWAY_THEN_INDEPENDENT_REVIEW"]["count"] == 5


def test_g5_9_split_no_ambiguity():
    g5 = _load("BATCH06_G5_FAILOVER_BACKUP_CLASSIFICATION.json")
    owned = g5["G5.9"]["batch06_owned_state_failover"]
    platform = g5["G5.9"]["platform_redis_postgresql_failover"]
    assert owned["classification"] == "NOT_APPLICABLE_WITH_ARCHITECTURE_JUSTIFICATION"
    assert platform["classification"] == "REQUIRES_RAILWAY"
    assert platform["railway_queue_ref"] == "RL6"


def test_g5_10_split_no_ambiguity():
    g5 = _load("BATCH06_G5_FAILOVER_BACKUP_CLASSIFICATION.json")
    owned = g5["G5.10"]["batch06_owned_durable_state"]
    platform = g5["G5.10"]["platform_postgresql_redis_durability_restore"]
    assert owned["classification"] == "NOT_APPLICABLE_WITH_ARCHITECTURE_JUSTIFICATION"
    assert platform["classification"] == "REQUIRES_RAILWAY"
    assert platform["railway_queue_ref"] == "RL7"


def test_api_abuse_rate_split():
    sec = _load("BATCH06_SECURITY_MATERIAL_PATH_AUDIT.json")
    split = sec["api_abuse_rate_split"]
    assert split["enforcement"]["status"] == "PROVEN_LOCAL"
    assert split["production_telemetry"]["status"] == "REQUIRES_RAILWAY"
    assert split["production_telemetry"]["railway_queue_ref"] == "RL4"
    assert sec["locally_solvable_gaps"] == 0


def test_consistency_assertions_all_pass():
    queues = _load("BATCH06_STATUS_QUEUES.json")
    assertions = queues["consistency_assertions"]
    assert assertions["all_pass"] is True
    assert assertions["no_locally_solvable_work_remains"] is True
    assert assertions["no_na_conflicts_with_active_platform_dependency"] is True
    assert assertions["no_independent_only_with_unmet_railway_prerequisite"] is True


def test_railway_queue_includes_rl6_rl7():
    queues = _load("BATCH06_STATUS_QUEUES.json")
    ids = {item["id"] for item in queues["QUEUE_B_RAILWAY_ONLY"]["items"]}
    assert ids == {"RL1", "RL2", "RL3", "RL4", "RL5", "RL6", "RL7"}


def test_rti_items_require_railway_prerequisites():
    queues = _load("BATCH06_STATUS_QUEUES.json")
    for item in queues["QUEUE_D_RAILWAY_THEN_INDEPENDENT_REVIEW"]["items"]:
        assert item["railway_evidence_required"] is True
        assert item["prerequisites"]
        assert item["why_not_independent_only"]
