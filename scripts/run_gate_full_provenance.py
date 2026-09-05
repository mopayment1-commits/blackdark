#!/usr/bin/env python3
"""Run test_institutional_gate_full with SLSA-style provenance attestation."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_gate_full_provenance() -> dict:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/cap646/test_institutional_gate.py::test_institutional_gate_full",
        "-q",
        "--tb=no",
    ]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    started_at = datetime.now(UTC).isoformat()
    t0 = time.perf_counter()
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    elapsed = round(time.perf_counter() - t0, 1)
    finished_at = datetime.now(UTC).isoformat()
    payload = {
        "attestation_id": "GATE_FULL_PROVENANCE",
        "command": " ".join(command),
        "commit_hash": commit,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "elapsed_seconds": elapsed,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-4000:] if proc.stdout else "",
        "stderr_tail": proc.stderr[-4000:] if proc.stderr else "",
    }
    (ROOT / "docs/GATE_FULL_PROVENANCE.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/GATE_FULL_LAST_EVIDENCE.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run_gate_full_provenance()
    print(json.dumps(result, indent=2))
    raise SystemExit(result["exit_code"])
