"""Operational completeness and live Gate Zero evidence tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def gate_live() -> dict:
    path = ROOT / "docs/BATCH05_GATE_ZERO_LIVE_EXECUTION.json"
    if not path.is_file():
        subprocess.run([sys.executable, str(ROOT / "scripts/execute_batch05_gate_zero_live.py")], cwd=ROOT, check=False)
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gap_report() -> dict:
    script = ROOT / "scripts/generate_batch05_operational_completeness_gap_report.py"
    subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)
    return json.loads((ROOT / "docs/BATCH05_OPERATIONAL_COMPLETENESS_GAP_REPORT.json").read_text(encoding="utf-8"))


def test_gate_zero_live_documented(gate_live: dict):
    assert gate_live["live_ready"] is False
    assert gate_live["pa_elevated_count"] == 0
    assert "health_probes" in gate_live
    assert gate_live["status"] in ("PASS", "FAILED")


def test_operational_completeness_no_inflation(gap_report: dict):
    assert gap_report["summary"]["operational_complete_count"] == 0
    assert gap_report["committee_submittable"] is False
    assert gap_report["live_ready"] is False
    assert gap_report["pa_elevated_count"] == 0
    assert gap_report["residual_7_institutional"]["deferred"] == 0
    assert all(not r["operational_complete"] for r in gap_report["rows"])
    assert all(not r["committee_ready"] for r in gap_report["rows"])


def test_residual_7_all_have_gaps_until_live(gap_report: dict):
    residual = {212, 206, 214, 226, 228, 232, 245}
    for row in gap_report["rows"]:
        if row["capability_id"] in residual:
            assert not row["operational_complete"]
            assert row["gaps"]
