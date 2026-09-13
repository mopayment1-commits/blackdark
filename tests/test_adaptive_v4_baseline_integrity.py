"""Adaptive v4 baseline freeze integrity tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_FINAL_LOCAL_BASELINE.json"
MANIFEST = ROOT / "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_EVIDENCE_MANIFEST.json"
CLOSURE = ROOT / "ADAPTIVE_V4_FINAL_LOCAL_CLOSURE.md"


def test_baseline_closure_artifacts_exist():
    assert BASELINE.is_file()
    assert MANIFEST.is_file()
    assert CLOSURE.is_file()
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert data["baseline_sha_short"] == "07bb4049"
    assert data["completion_state"]["ADAPTIVE_V4_FINAL_LOCAL_COMPLETION"] is True
    assert data["locally_remediable_remaining"] == 0


def test_baseline_integrity_gate_passes():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/adaptive_v4_baseline_integrity.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    result = json.loads(proc.stdout)
    assert proc.returncode == 0, result
    assert result["BASELINE_INTEGRITY_VERIFIED"] is True
