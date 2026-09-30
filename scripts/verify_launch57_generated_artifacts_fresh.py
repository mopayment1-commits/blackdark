#!/usr/bin/env python3
"""Ensure generated Launch-57 status files are in sync with evidence index (CI hygiene)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
STATUS = ROOT / "governance" / "launch57" / "LAUNCH57_COMPLETION_STATUS.json"
ENGINEERING = ROOT / "governance/launch57/LAUNCH57_ENGINEERING_CLOSURE.json"
GATE_INDEX = ROOT / "governance/launch57/LAUNCH57_REMEDIATION_GATE_INDEX.json"


def main() -> int:
    if not INDEX.is_file():
        return 1
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    idx_sha = idx.get("remediation_sha")
    idx_phase = idx.get("phase")
    errors: list[str] = []
    for path in (STATUS, ENGINEERING):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("remediation_sha") != idx_sha:
            errors.append(f"{path.name}: remediation_sha drift (index={idx_sha}, file={data.get('remediation_sha')})")
        if path == STATUS and data.get("phase") != idx_phase:
            errors.append(f"{path.name}: phase drift (index={idx_phase}, file={data.get('phase')})")
    if GATE_INDEX.is_file():
        gi = json.loads(GATE_INDEX.read_text(encoding="utf-8"))
        if gi.get("remediation_sha") != idx_sha:
            errors.append(f"gate index remediation_sha drift (index={idx_sha}, file={gi.get('remediation_sha')})")
        if gi.get("phase") != idx_phase:
            errors.append(f"gate index phase drift (index={idx_phase}, file={gi.get('phase')})")
    elif idx.get("remediation_gate_index"):
        errors.append("missing LAUNCH57_REMEDIATION_GATE_INDEX.json")
    if errors:
        print("ARTIFACT_STALE:", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        print(
            "Run: python scripts/generate_launch57_completion_status.py && "
            "python scripts/generate_launch57_engineering_closure.py && "
            "python scripts/generate_launch57_gate_index.py",
            file=sys.stderr,
        )
        return 1
    print("PASS: completion artifacts match evidence index remediation_sha")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
