#!/usr/bin/env python3
"""Verify finding evidence is indexed and normative IDs match institutional program register."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
TRACE = ROOT / "governance" / "launch57" / "LAUNCH57_NORMATIVE_TRACEABILITY.json"
LOCK = ROOT / "governance/launch57/FINDING_INVENTORY_LOCK.json"
PROGRAM = ROOT / "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md"
SKIP = ("GET ", "POST ")


def main() -> int:
    if not all(p.is_file() for p in (INDEX, TRACE, LOCK, PROGRAM)):
        print("MISSING required institutional files", file=sys.stderr)
        return 1
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    lock_ids = list((json.loads(LOCK.read_text(encoding="utf-8"))).get("expected_ids") or [])
    allowed = set(trace.get("allowed_normative_ids") or [])
    errors: list[str] = []
    findings_index = index.get("findings") or {}
    findings_trace = trace.get("findings") or {}
    if sorted(findings_index.keys()) != sorted(lock_ids):
        errors.append("evidence index keys differ from FINDING_INVENTORY_LOCK")
    if sorted(findings_trace.keys()) != sorted(lock_ids):
        errors.append("traceability keys differ from FINDING_INVENTORY_LOCK")
    for fid in lock_ids:
        trow = findings_trace.get(fid) or {}
        irow = findings_index.get(fid) or {}
        for nid in trow.get("normative") or []:
            if nid not in allowed:
                errors.append(f"{fid}: normative id {nid} not in program §2 register")
        evidence = irow.get("evidence") or []
        paths = [e for e in evidence if isinstance(e, str) and not e.startswith(SKIP)]
        if not paths:
            errors.append(f"{fid}: no repo evidence paths in index")
        for rel in paths:
            if not (ROOT / rel).is_file():
                errors.append(f"{fid}: missing evidence file {rel}")
        status = str(irow.get("status", ""))
        if status.startswith("OPEN") and fid in {"FINDING-01", "FINDING-18", "FINDING-19"}:
            continue
        if status == "CLOSED_REPO" and fid == "FINDING-14":
            continue
        if status == "CLOSED_PARTIAL" and fid == "FINDING-11":
            continue
    if errors:
        print("NORMATIVE_TRACEABILITY_FAIL:", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"PASS: {len(lock_ids)} findings traced to {PROGRAM.name} with on-disk evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
