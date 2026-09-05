#!/usr/bin/env python3
"""Compute weighted statement coverage for official spine modules (CLOSURE-MANDATE-FINAL item 13/20)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cobertura_spine import parse_spine_coverage

ROOT = Path(__file__).resolve().parents[1]
SPINE_MODULES = [
    "cap646/runtime.py",
    "cap646/batch_spine.py",
    "cap646/batch01_production.py",
    "cap646/batch01_dedicated.py",
    "cap646/batch02_production.py",
    "cap646/batch02_dedicated.py",
    "database.py",
]


def main() -> int:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/cap646/test_closure_reject_04.py",
            "tests/cap646/test_institutional_gate.py",
            "tests/test_bigquery_export_mock.py",
            "--cov=cap646",
            "--cov=database",
            "--cov-report=xml:coverage.xml",
            "-q",
            "--tb=no",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    cov_path = ROOT / "coverage.xml"
    if not cov_path.exists():
        print(json.dumps({"error": "coverage.xml missing", "pytest_rc": proc.returncode}))
        return 1
    parsed = parse_spine_coverage(cov_path, SPINE_MODULES)
    out = {**parsed, "pytest_exit_code": proc.returncode}
    (ROOT / "docs/SPINE_COVERAGE_SNAPSHOT.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
