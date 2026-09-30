#!/usr/bin/env python3
"""Validate open/partial ops closure package matches evidence index (program §3.3 / §8.1 honesty)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"


def _status_ok(actual: str, spec: dict) -> bool:
    if spec.get("status_expected"):
        return actual in spec["status_expected"]
    prefixes = spec.get("status_expected_prefixes") or []
    return any(actual.startswith(p) for p in prefixes)


def main() -> int:
    if not PKG.is_file() or not INDEX.is_file():
        print("MISSING package or index", file=sys.stderr)
        return 1
    pkg = json.loads(PKG.read_text(encoding="utf-8"))
    if pkg.get("program_complete_81"):
        print("package must not claim program_complete_81", file=sys.stderr)
        return 1
    index_findings = json.loads(INDEX.read_text(encoding="utf-8")).get("findings") or {}
    errors: list[str] = []
    open_pkg = pkg.get("open_or_partial_findings") or {}
    for fid, spec in open_pkg.items():
        irow = index_findings.get(fid)
        if not irow:
            errors.append(f"{fid}: not in evidence index")
            continue
        st = str(irow.get("status", ""))
        if st == "CLOSED":
            errors.append(f"{fid}: index CLOSED but still listed in open ops package — update package")
        if not _status_ok(st, spec):
            errors.append(f"{fid}: status {st} does not match package expectation")
        for script in spec.get("operator_scripts") or []:
            if script.endswith(".py") and not (ROOT / script).is_file():
                errors.append(f"{fid}: missing script {script}")
        idx_req = (irow.get("closure_requires") or irow.get("note") or "").strip()
        pkg_req = (spec.get("closure_requires") or "").strip()
        if idx_req and pkg_req and idx_req != pkg_req:
            errors.append(f"{fid}: closure_requires drift vs index")
    for script in pkg.get("aggregate_gates") or []:
        if not (ROOT / script).is_file():
            errors.append(f"missing aggregate gate {script}")
    closed_in_index = [fid for fid, row in index_findings.items() if row.get("status") == "CLOSED"]
    missing_from_pkg = [fid for fid in closed_in_index if fid in open_pkg]
    if missing_from_pkg:
        errors.append(f"CLOSED findings still in package: {missing_from_pkg}")
    if errors:
        print("OPEN_OPS_PACKAGE_FAIL:", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"PASS: open ops package aligned with index ({len(open_pkg)} tracked findings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
