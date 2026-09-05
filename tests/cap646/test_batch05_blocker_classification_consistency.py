"""Machine-readable consistency tests for Batch05 blocker classification taxonomy."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> dict:
    return json.loads((ROOT / "docs" / name).read_text(encoding="utf-8"))


def test_status_queues_four_taxonomy():
    queues = _load("BATCH05_STATUS_QUEUES.json")
    assert "QUEUE_A_LOCAL_COMPLETE" in queues
    assert "QUEUE_B_RAILWAY_ONLY" in queues
    assert "QUEUE_C_INDEPENDENT_REVIEW_ONLY" in queues
    assert "QUEUE_D_RAILWAY_THEN_INDEPENDENT_REVIEW" in queues
    assert queues["QUEUE_C_INDEPENDENT_REVIEW_ONLY"]["count"] == 0
    assert queues["QUEUE_D_RAILWAY_THEN_INDEPENDENT_REVIEW"]["count"] == 5


def test_g5_9_split_no_ambiguity():
    g5 = _load("BATCH05_G5_FAILOVER_BACKUP_CLASSIFICATION.json")
    owned = g5["G5.9"]["batch05_owned_state_failover"]
    platform = g5["G5.9"]["platform_redis_postgresql_failover"]
    assert owned["classification"] == "NOT_APPLICABLE_WITH_ARCHITECTURE_JUSTIFICATION"
    assert platform["classification"] == "REQUIRES_RAILWAY"
    assert platform["railway_queue_ref"] == "RL6"


def test_g5_10_split_no_ambiguity():
    g5 = _load("BATCH05_G5_FAILOVER_BACKUP_CLASSIFICATION.json")
    owned = g5["G5.10"]["batch05_owned_durable_state"]
    platform = g5["G5.10"]["platform_postgresql_redis_durability_restore"]
    assert owned["classification"] == "NOT_APPLICABLE_WITH_ARCHITECTURE_JUSTIFICATION"
    assert platform["classification"] == "REQUIRES_RAILWAY"
    assert platform["railway_queue_ref"] == "RL7"


def test_api_abuse_rate_split():
    sec = _load("BATCH05_SECURITY_MATERIAL_PATH_AUDIT.json")
    split = sec["api_abuse_rate_split"]
    assert split["enforcement"]["status"] == "PROVEN_LOCAL"
    assert split["production_telemetry"]["status"] == "REQUIRES_RAILWAY"
    assert split["production_telemetry"]["railway_queue_ref"] == "RL4"
    assert sec["locally_solvable_gaps"] == 0


def test_consistency_assertions_all_pass():
    queues = _load("BATCH05_STATUS_QUEUES.json")
    assertions = queues["consistency_assertions"]
    assert assertions["all_pass"] is True
    assert assertions["dependency_graph_node_count"] == 12
    assert assertions["blocker_registry_count"] == 12
    assert assertions["reported_node_count_equals_actual"] is True
    assert assertions["zero_cycles"] is True
    assert assertions["live_ready_separated_from_assurance_ready"] is True


def test_railway_queue_includes_rl6_rl7():
    queues = _load("BATCH05_STATUS_QUEUES.json")
    ids = {item["id"] for item in queues["QUEUE_B_RAILWAY_ONLY"]["items"]}
    assert ids == {"RL1", "RL2", "RL3", "RL4", "RL5", "RL6", "RL7"}


def test_rti5_assurance_only_not_live_ready():
    queues = _load("BATCH05_STATUS_QUEUES.json")
    rti5 = next(i for i in queues["QUEUE_D_RAILWAY_THEN_INDEPENDENT_REVIEW"]["items"] if i["id"] == "RTI5")
    assert rti5["underlying"] == ["ASSURANCE_READY"]
    assert rti5["prerequisites"] == ["RTI4"]


def test_live_ready_status_node_in_graph():
    queues = _load("BATCH05_STATUS_QUEUES.json")
    node_ids = {n["node_id"] for n in queues["dependency_graph"]}
    assert "STATUS_LIVE_READY" in node_ids
    assert len(node_ids) == 12


def test_freeze_head_consistency():
    import sys

    sys.path.insert(0, str(ROOT))
    from scripts.assert_batch05_freeze_head_consistency import build

    freeze = _load("BATCH05_FINAL_LOCAL_FREEZE.json")
    heads = freeze["freeze_heads"]
    assert heads["repository_head"] == heads["artifact_generation_head"]
    assert heads["repository_head"] == heads["artifact_embedded_head"]
    assert heads["source_head"] == heads["final_freeze_head"]
    assert heads["repository_head"] == heads["source_head"]
    assert heads.get("tested_source_head", heads["source_head"]) == heads["source_head"]
    assert freeze["git_commit"] == heads["source_head"]
    assert freeze["BATCH05_FINAL_LOCAL_FREEZE"] is freeze["LOCAL_GOVERNANCE_COMPLETE"]
    if freeze["BATCH05_FINAL_LOCAL_FREEZE"] is True:
        assert freeze.get("known_local_deficiencies") == []
        assert freeze["sonarcloud"]["quality_gate_status"] in {"OK", "PASS"}
        assert freeze["sonarcloud"].get("quality_gate_pass") is True

    ancestry = build()
    assert ancestry["production_runtime_drift_count"] == 0
    assert ancestry["frozen_source_head_is_semantically_equivalent_to_current_head"] is True
    for row in ancestry["commits_since_tested_source"]:
        assert row["role"] in {
            "docs_stamp",
            "evidence_docs_tests_scripts",
            "dependency_lock_change",
        }
        assert row["production_runtime_files"] == []
    assert freeze.get("warnings_local_solvable", []) == []
    assert freeze.get("frozen_source_head_is_semantically_equivalent_to_current_head") is True


def test_col10_preparation_50_of_50():
    col10 = _load("BATCH05_PENTAGONAL_COL10_PREPARATION.json")
    assert col10["summary"]["local_preparation_complete"] == 50
    assert col10["summary"]["independent_signoff_pending"] == 50


def test_col5_collective_review_local_complete():
    pent = _load("BATCH05_PENTAGONAL_TEMPLATE_201_250.json")
    complete = sum(
        1
        for r in pent["rows"]
        if r.get("pentagonal", {}).get("collective_review_local", {}).get("status") == "LOCAL_COMPLETE"
    )
    assert complete == 50


def test_domain_rules_all_pass_50():
    pent = _load("BATCH05_PENTAGONAL_TEMPLATE_201_250.json")
    assert pent.get("domain_rules_all_pass_count", 0) == 50


def test_12207_validation_local_complete():
    val = _load("BATCH05_12207_VALIDATION_PACKAGE.json")
    assert val["status"] == "LOCAL_COMPLETE"
    assert val["summary"]["local_complete"] == 50


def test_per_id_matrix_50_rows():
    matrix = _load("BATCH05_PER_ID_FINAL_MATRIX_201_250.json")
    rows = matrix.get("rows") or matrix.get("per_id")
    assert len(rows) == 50
    gaps = matrix.get("locally_solvable_gaps_total", matrix.get("summary", {}).get("locally_solvable_gaps_total"))
    assert gaps == 0


def test_per_id_classification_partition_exact():
    import sys

    sys.path.insert(0, str(ROOT))
    from cap646.batch05_dedicated import BATCH05_REUSED_LINK_IDS
    from cap646.batch05_ids import BATCH05_DUPLICATE_DELEGATION_IDS, BATCH05_MANIFEST_IDS
    from scripts.batch05_classification_partition import (
        CLOSED_DUPLICATE_DELEGATION_IDS,
        CLOSED_REUSED_LINK_IDS,
        assert_runtime_sets,
        partition_from_rows,
    )

    matrix = _load("BATCH05_PER_ID_FINAL_MATRIX_201_250.json")
    rows = matrix["rows"]
    part = partition_from_rows(rows)
    assertions = part["assertions"]
    unique_ids = assertions["unique_ids"]
    duplicate_classification_ids = assertions["duplicate_classification_ids"]
    missing_ids = assertions["missing_ids"]
    classification_total = assertions["classification_total"]
    assert unique_ids == 50
    assert duplicate_classification_ids == []
    assert missing_ids == []
    assert classification_total == 50
    assert part["counts"] == {
        "STRANGLER": 43,
        "CLOSED_REUSED_LINK": 6,
        "CLOSED_DUPLICATE_DELEGATION": 1,
    }
    assert part["CLOSED_DUPLICATE_DELEGATION"]["ids"] == [212]
    assert 212 not in part["CLOSED_REUSED_LINK"]["ids"]
    assert part["CLOSED_REUSED_LINK"]["ids"] == [206, 214, 226, 228, 232, 245]
    assert assertions["all_pass"] is True
    stored = matrix.get("classification")
    assert stored is not None
    assert stored["assertions"]["all_pass"] is True
    assert stored["counts"] == part["counts"]
    assert_runtime_sets(BATCH05_REUSED_LINK_IDS, BATCH05_DUPLICATE_DELEGATION_IDS, BATCH05_MANIFEST_IDS)
    assert CLOSED_REUSED_LINK_IDS == frozenset({206, 214, 226, 228, 232, 245})
    assert CLOSED_DUPLICATE_DELEGATION_IDS == frozenset({212})

    queues = _load("BATCH05_STATUS_QUEUES.json")
    reused_item = next(
        i for i in queues["QUEUE_A_LOCAL_COMPLETE"]["items"] if i["category"] == "REUSED-LINK / duplicate"
    )
    assert "212" in reused_item["status"] and "DUPLICATE" in reused_item["status"]
    assert reused_item.get("reused_link_ids") == [206, 214, 226, 228, 232, 245]
    assert reused_item.get("duplicate_delegation_ids") == [212]
    assert "206, 212, 214" not in reused_item["status"]
