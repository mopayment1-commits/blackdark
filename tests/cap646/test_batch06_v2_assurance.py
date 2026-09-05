"""Batch06 v2 assurance + final local freeze contract."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_final_local_freeze_complete():
    path = ROOT / "docs/BATCH06_FINAL_LOCAL_FREEZE.json"
    if not path.is_file():
        subprocess.run([sys.executable, str(ROOT / "scripts/generate_batch06_final_local_freeze.py")], cwd=ROOT, check=True)
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["g0_g4"]["G4"] == 50
    assert doc["semantic_oracle"] == 50
    assert doc["reliability"]["requires_live"] == 0
    assert doc["reliability"]["status"] == "PROVEN_LOCAL"
    assert doc["global_duplicate_review"]["unresolved_local_conflicts"] == 0
    assert doc["live_ready"] is False
    assert doc["assurance_ready"] is False


def test_v2_package_gate_counts():
    path = ROOT / "docs/BATCH06_V2_ASSURANCE_PACKAGE.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    gc = doc["gate_counts"]
    assert gc["G4_verification_validation"]["PASS_ENGINEERING"] == 50
    assert doc["verdict"]["final_status"] == "BLOCKED_EXTERNAL_FOR_LIVE_ONLY"
    assert doc["batch06_independent"] == 0
    assert doc["progress_826"] == 179
