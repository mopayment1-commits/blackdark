"""Contract tests for Batch05 residual 7 institutional disposition."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/generate_batch05_residual_7_disposition.py"
OUT = ROOT / "docs/BATCH05_RESIDUAL_7_INSTITUTIONAL_DISPOSITION.json"
RESIDUAL = {212, 206, 214, 226, 228, 232, 245}


@pytest.fixture(scope="module")
def doc() -> dict:
    if not OUT.is_file():
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_residual_7_all_decided(doc: dict):
    assert doc["summary"]["deferred"] == 0
    assert doc["summary"]["total"] == 7
    assert doc["pa_elevated_count"] == 0
    ids = {r["capability_id"] for r in doc["rows"]}
    assert ids == RESIDUAL


def test_residual_7_decision_mix(doc: dict):
    assert doc["summary"]["closed_reused_link"] == 4
    assert doc["summary"]["closed_duplicate_delegation"] == 1
    assert doc["summary"]["closed_tolerate_dual_path"] == 2


def test_residual_7_per_id_analysis(doc: dict):
    for row in doc["rows"]:
        assert row["mece"]["mece_verdict"]
        assert row["type4_behavioral_comparison"]["all_surfaces_match_canonical"]
        assert row["canonical_25010_complete"]["verified_locally"]
        assert row["six_heroes_impact"]["hero_eliminated"]
        assert not row["pa_elevated"]
        if row["capability_id"] in (214, 245):
            assert row["tolerate_ceiling"] == "2026-12-31"
            assert row["tolerate_exit_criteria"]


def test_residual_7_stamped_acceptance(doc: dict):
    acc = json.loads((ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json").read_text(encoding="utf-8"))
    for cid in RESIDUAL:
        row = next(r for r in acc["rows"] if r["capability_id"] == cid)
        assert "residual_7_disposition" in row
        assert row["residual_7_disposition"]["institutional_decision"]
