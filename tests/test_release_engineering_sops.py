"""Release engineering SOP gate smoke tests (#30, #31)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_release_chaos_gate_dry_run():
    proc = _run("release_chaos_gate.py", "--dry-run")
    assert proc.returncode == 0
    log = ROOT / "data" / "release_engineering" / "chaos_experiments.jsonl"
    assert log.is_file()
    last = json.loads(log.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert last.get("sop") == "#31_chaos_failure_injection"
    assert last.get("release_pass") is True
    assert last.get("fail_closed_verified") is True


def test_release_capacity_evidence_dry_run():
    proc = _run("release_capacity_evidence.py", "--dry-run")
    assert proc.returncode == 0
    log = ROOT / "data" / "release_engineering" / "capacity_trend.jsonl"
    assert log.is_file()
    last = json.loads(log.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert last.get("sop") == "#30_capacity_load_evidence"
    assert last.get("no_user_extrapolation") is True


def test_release_engineering_gate_dry_run():
    proc = _run("release_engineering_gate.py", "--dry-run", "--skip-capacity")
    assert proc.returncode == 0
    report = json.loads((ROOT / "data" / "release_engineering" / "release_gate_latest.json").read_text())
    assert report.get("release_pass") is True
    assert "#32_circuit_breakers" in report.get("sops", [])
