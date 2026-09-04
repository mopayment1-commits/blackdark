"""Contract tests for Batch05 PA closure sweep artifact (43 strangler IDs)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SWEEP_JSON = ROOT / "docs/BATCH05_PA_CLOSURE_SWEEP_43.json"
SCRIPT = ROOT / "scripts/generate_batch05_pa_closure_sweep.py"

from cap646.batch05_strangler_spine import STRANGLER_IMPLEMENTED_IDS  # noqa: E402


@pytest.fixture(scope="module")
def sweep_doc() -> dict:
    if not SWEEP_JSON.is_file():
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    return json.loads(SWEEP_JSON.read_text(encoding="utf-8"))


def test_pa_sweep_locks(sweep_doc: dict):
    assert sweep_doc["pa_elevated_count"] == 0
    assert sweep_doc["production_aligned_count"] == 0
    assert sweep_doc["batch05_independent"] == 0
    assert sweep_doc["progress_826"] == 179
    assert sweep_doc["sequence_item"] == 1
    assert len(sweep_doc["elevation_log"]) == 0


def test_pa_sweep_covers_all_stranglers(sweep_doc: dict):
    ids = {r["capability_id"] for r in sweep_doc["rows"]}
    assert ids == STRANGLER_IMPLEMENTED_IDS
    assert len(ids) == 43


def test_pa_sweep_five_columns_per_row(sweep_doc: dict):
    required_cols = {
        "col6_iso25010_completeness_correctness_appropriateness",
        "col7_iso29148_expected_output",
        "col8_iso29119_e2e_interface",
        "col9_owasp_asvs_security",
        "col10_sre_prr_collective_review",
    }
    for row in sweep_doc["rows"]:
        pent = row["pentagonal_five_columns"]
        assert required_cols <= set(pent)
        assert row["pa_elevated"] is False
        assert row["production_aligned"] is False
        eo = row["expected_output_comparison"]
        assert eo["comparison_source"] == "live_probe_execute_capability"
        assert "rule_results" in eo


def test_pa_sweep_domain_rules_all_pass(sweep_doc: dict):
    assert sweep_doc["summary"]["domain_all_pass_count"] == 43
    for row in sweep_doc["rows"]:
        assert row["domain_all_pass"] is True
        assert row["pa_closure_phase"] == "VERIFICATION_LOCAL"
        assert row["pa_eligible"] is False
        assert len(row["pa_blockers"]) >= 5
