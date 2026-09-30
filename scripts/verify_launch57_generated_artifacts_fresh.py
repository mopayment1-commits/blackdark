#!/usr/bin/env python3
"""Ensure generated Launch-57 status files are in sync with evidence index (CI hygiene)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
STATUS = ROOT / "governance" / "launch57" / "LAUNCH57_COMPLETION_STATUS.json"
ENGINEERING = ROOT / "governance" / "launch57" / "LAUNCH57_ENGINEERING_CLOSURE.json"


def main() -> int:
    if not INDEX.is_file():
        return 1
    idx_sha = json.loads(INDEX.read_text(encoding="utf-8")).get("remediation_sha")
    errors: list[str] = []
    for path in (STATUS, ENGINEERING):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("remediation_sha") != idx_sha:
            errors.append(f"{path.name}: remediation_sha drift (index={idx_sha}, file={data.get('remediation_sha')})")
    if errors:
        print("ARTIFACT_STALE:", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        print("Run: python scripts/generate_launch57_completion_status.py && python scripts/generate_launch57_engineering_closure.py", file=sys.stderr)
        return 1
    print("PASS: completion artifacts match evidence index remediation_sha")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
