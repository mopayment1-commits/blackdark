"""Production readiness closure regression tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_readiness_closure_runs():
    proc = subprocess.run(
        [sys.executable, "scripts/production_readiness_closure.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["verdict"] in {
        "CAPABILITY_PRODUCTION_READINESS_ENGINEERING_CLOSED_WITH_GENUINE_EXTERNAL_GATES",
        "CAPABILITY_PRODUCTION_READINESS_ENGINEERING_CLOSED",
    }
    counters = payload["counters"]
    assert counters["PASS_ENGINEERING"] == 932
    assert counters["LOCAL_ENGINEERING_GAPS"] == 0
    assert counters["PR_REQUIREMENTS_GAPS"] == 0


def test_production_readiness_independent_verifier():
    subprocess.run([sys.executable, "scripts/production_readiness_closure.py"], cwd=ROOT, check=True, timeout=900)
    proc = subprocess.run(
        [sys.executable, "scripts/production_readiness_independent_verifier.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    out = json.loads(proc.stdout)
    assert out["independent_ok"] is True
    assert out["PR_INDEPENDENT_VERIFIER_SELF_REFERENCE"] == 0
    assert out["PASS_ENGINEERING"] == 932
