#!/usr/bin/env python3
"""Compute weighted statement coverage for official spine modules (CLOSURE-MANDATE-FINAL item 13/20)."""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

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
    root = ET.parse(cov_path)
    rows = []
    total_stmts = total_miss = 0
    for rel in SPINE_MODULES:
        cls = root.find(f".//class[@filename='{rel.split('/')[-1]}']")
        if cls is None:
            rows.append({"module": rel, "stmts": 0, "miss": 0, "coverage_pct": None})
            continue
        rate = float(cls.get("line-rate", 0))
        line_nodes = cls.findall("lines/line")
        if line_nodes:
            stmts = len(line_nodes)
            miss = sum(1 for ln in line_nodes if int(ln.get("hits", 0)) == 0)
        else:
            stmts = int(float(cls.get("line-rate", 0)) and 0)  # fallback unused
            stmts = len(line_nodes) or max(1, int(1 / rate)) if rate else 0
            miss = int(round(stmts * (1 - rate)))
        total_stmts += stmts
        total_miss += miss
        pct = round(100 * (stmts - miss) / stmts, 2) if stmts else 0
        rows.append({"module": rel, "stmts": stmts, "miss": miss, "coverage_pct": pct})
    weighted = round(100 * (total_stmts - total_miss) / total_stmts, 2) if total_stmts else 0
    out = {
        "spine_modules": rows,
        "combined_spine": {
            "total_stmts": total_stmts,
            "total_miss": total_miss,
            "weighted_statement_coverage_pct": weighted,
            "metric": "statement_coverage_not_branch",
        },
        "pytest_exit_code": proc.returncode,
    }
    (ROOT / "docs/SPINE_COVERAGE_SNAPSHOT.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
