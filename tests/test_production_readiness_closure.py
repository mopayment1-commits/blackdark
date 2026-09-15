"""Production readiness closure regression tests — 161 governing gates."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_governing_catalog_has_161_requirements():
    sys.path.insert(0, str(ROOT / "scripts"))
    from production_readiness_governing_catalog import governing_requirements

    assert len(governing_requirements()) == 161


def test_production_readiness_closure_runs():
    proc = subprocess.run(
        [sys.executable, "scripts/production_readiness_closure.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    counters = payload["counters"]
    assert counters["GOVERNING_PR_REQUIREMENTS_DISCOVERED"] == 161
    assert counters["TRACEABILITY_MATRIX_REQUIREMENTS"] == 161
    assert counters["PASS_ENGINEERING"] == 932
    assert counters["LOCAL_ENGINEERING_GAPS"] == 0
    assert counters["PR_REQUIREMENTS_GAPS"] == 0
    assert counters["COLLAPSED_REQUIREMENTS_WITH_LOST_SEMANTICS"] == 0
    assert payload["integrity_verdict"] == "PRODUCTION_READINESS_FINAL_INTEGRITY_VERIFIED"


def test_production_readiness_independent_verifier():
    subprocess.run([sys.executable, "scripts/production_readiness_closure.py"], cwd=ROOT, check=True, timeout=1800)
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
    assert out["PR_INDEPENDENT_REQUIREMENTS_RECOMPUTED"] == 161
    assert out["PASS_ENGINEERING"] == 932
