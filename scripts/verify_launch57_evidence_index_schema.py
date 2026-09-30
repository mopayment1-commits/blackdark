#!/usr/bin/env python3
"""Program §9 — evidence index structural validation (no closure claims)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "governance/launch57/LAUNCH57_EVIDENCE_INDEX_SCHEMA.json"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"
LOCK = ROOT / "governance/launch57/FINDING_INVENTORY_LOCK.json"


def main() -> int:
    if not all(p.is_file() for p in (SCHEMA, INDEX, LOCK)):
        print("MISSING schema, index, or lock", file=sys.stderr)
        return 1
    spec = json.loads(SCHEMA.read_text(encoding="utf-8"))
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    lock_ids = list(json.loads(LOCK.read_text(encoding="utf-8")).get("expected_ids") or [])
    errors: list[str] = []
    for key in spec.get("required_top_level") or []:
        if key not in idx:
            errors.append(f"missing top-level key {key}")
    if idx.get("program") != spec.get("program_name_expected"):
        errors.append("program name mismatch")
    if idx.get("baseline_sha") != spec.get("baseline_sha_expected"):
        errors.append("baseline_sha must remain inventory baseline")
    findings = idx.get("findings") or {}
    if len(findings) != spec.get("finding_count"):
        errors.append(f"expected {spec.get('finding_count')} findings")
    if sorted(findings.keys()) != sorted(lock_ids):
        errors.append("finding ids differ from inventory lock")
    for fid in lock_ids:
        row = findings.get(fid) or {}
        for field in spec.get("required_finding_fields") or []:
            if field not in row:
                errors.append(f"{fid}: missing {field}")
        if not row.get("evidence"):
            errors.append(f"{fid}: empty evidence")
    if errors:
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("PASS: evidence index matches program §9 schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
