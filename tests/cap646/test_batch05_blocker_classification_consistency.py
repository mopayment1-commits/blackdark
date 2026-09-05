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
    import subprocess

    freeze = _load("BATCH05_FINAL_LOCAL_FREEZE.json")
    heads = freeze["freeze_heads"]
    assert heads["repository_head"] == heads["artifact_generation_head"]
    assert heads["repository_head"] == heads["artifact_embedded_head"]
    assert heads["source_head"] == heads["final_freeze_head"]
    assert heads["repository_head"] == heads["source_head"]
    assert freeze["git_commit"] == heads["source_head"]
    assert freeze["BATCH05_FINAL_LOCAL_FREEZE"] is True

    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    source = heads["source_head"]
    if current != source:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source, current],
            cwd=ROOT,
            check=True,
        )
        diff_names = subprocess.check_output(
            ["git", "diff", "--name-only", source, current],
            cwd=ROOT,
            text=True,
        ).strip().splitlines()
        allowed = {
            "tests/cap646/test_batch05_blocker_classification_consistency.py",
        }
        for name in diff_names:
            assert name.startswith("docs/BATCH05_") or name == (
                "tests/cap646/test_batch05_blocker_classification_consistency.py"
            ), f"unexpected drift file: {name}"


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
