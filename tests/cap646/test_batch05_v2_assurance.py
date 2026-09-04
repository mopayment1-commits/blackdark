"""Batch05 v2 institutional assurance package tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def v2_package() -> dict:
    script = ROOT / "scripts/generate_batch05_v2_assurance_package.py"
    subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)
    return json.loads((ROOT / "docs/BATCH05_V2_ASSURANCE_PACKAGE.json").read_text(encoding="utf-8"))


def test_v2_no_counter_inflation(v2_package: dict):
    assert v2_package["batch05_independent"] == 0
    assert v2_package["progress_826"] == 179
    assert v2_package["production_aligned_count"] == 0
    assert v2_package["pa_elevated_count"] == 0
    assert v2_package["live_ready"] is False
    assert v2_package["assurance_ready"] is False


def test_v2_blocked_external_verdict(v2_package: dict):
    assert v2_package["verdict"]["final_status"] == "BLOCKED_EXTERNAL"
    assert v2_package["verdict"]["assurance_ready_count"] == 0
    assert v2_package["live_e2e"]["proven_count"] == 0


def test_v2_per_id_matrix_complete(v2_package: dict):
    matrix = v2_package["per_id_closure_matrix"]
    assert len(matrix) == 50
    ids = {r["capability_id"] for r in matrix}
    assert ids == set(range(201, 251))
    for row in matrix:
        assert len(row["gates"]) == 8
        assert row["gates"]["G6_live_validation"] == "BLOCKED_EXTERNAL"
        assert row["assurance_ready"] is False


def test_semantic_oracle_not_weak_only():
    doc = json.loads((ROOT / "docs/BATCH05_SEMANTIC_ORACLE_VERIFICATION.json").read_text(encoding="utf-8"))
    assert doc["summary"]["weak_only_rule_ids"] == 0
    assert doc["summary"]["semantic_verified_local"] >= 48


def test_canonical_residual_7_preserved():
    doc = json.loads((ROOT / "docs/BATCH05_CANONICAL_DUPLICATE_ASSURANCE.json").read_text(encoding="utf-8"))
    assert doc["summary"]["residual_7_routing_pass"] is True
    assert doc["summary"]["deferred"] == 0
    tolerate = [r for r in doc["residual_7"] if r["institutional_decision"] == "CLOSED_TOLERATE_DUAL_PATH"]
    assert {r["capability_id"] for r in tolerate} == {214, 245}
    for r in tolerate:
        assert r["tolerate_ceiling"] == "2026-12-31"


def test_production_root_cause_documented():
    doc = json.loads((ROOT / "docs/BATCH05_PRODUCTION_ROOT_CAUSE.json").read_text(encoding="utf-8"))
    assert doc["root_cause_classification"] == "DEPLOYMENT_NOT_ATTACHED"
    assert doc["repair_executable_by_agent"] is False
    assert "minimum_owner_action" in doc
