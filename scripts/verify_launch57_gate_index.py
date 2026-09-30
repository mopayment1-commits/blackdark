#!/usr/bin/env python3
"""Verify gate index matches evidence index and all gate paths exist on disk."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"
GATES = ROOT / "governance/launch57/LAUNCH57_REMEDIATION_GATE_INDEX.json"


def main() -> int:
    if not INDEX.is_file() or not GATES.is_file():
        print("MISSING index or gate index", file=sys.stderr)
        return 1
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    data = json.loads(GATES.read_text(encoding="utf-8"))
    if data.get("cisa_certification_claimed"):
        print("gate index must not claim certification", file=sys.stderr)
        return 1
    if data.get("remediation_sha") != idx.get("remediation_sha"):
        print("gate index remediation_sha drift — run generate_launch57_gate_index.py", file=sys.stderr)
        return 1
    if data.get("phase") != idx.get("phase"):
        print("gate index phase drift — run generate_launch57_gate_index.py", file=sys.stderr)
        return 1
    errors: list[str] = []
    indexed_paths = {
        rel
        for key, rel in idx.items()
        if isinstance(rel, str) and (key.endswith("_gate") or key in {"ops_playbook_dry_run", "ops_closure_gate"})
    }
    gate_paths = {g.get("path") for g in data.get("gates") or [] if g.get("path")}
    for rel in indexed_paths:
        if rel not in gate_paths:
            errors.append(f"index gate missing from gate index: {rel}")
    for g in data.get("gates") or []:
        rel = str(g.get("path", ""))
        if not rel:
            errors.append(f"empty path in gate {g.get('id')}")
            continue
        if not (ROOT / rel).is_file():
            errors.append(f"missing file {rel}")
    if errors:
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"PASS: {len(gate_paths)} gates indexed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
