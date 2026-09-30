#!/usr/bin/env python3
"""Program §8.1 — report program complete only when all 19 findings are status CLOSED (exact)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
LOCK = ROOT / "governance/launch57/FINDING_INVENTORY_LOCK.json"


def main() -> int:
    if not INDEX.is_file() or not LOCK.is_file():
        print("MISSING index or inventory lock", file=sys.stderr)
        return 1
    lock_ids = list(json.loads(LOCK.read_text(encoding="utf-8")).get("expected_ids") or [])
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    findings = index.get("findings") or {}
    not_closed: dict[str, str] = {}
    for fid in lock_ids:
        st = str((findings.get(fid) or {}).get("status", "MISSING"))
        if st != "CLOSED":
            not_closed[fid] = st
    program_complete_81 = len(not_closed) == 0
    report = {
        "authority": "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md",
        "program_section": "§8.1 Program complete",
        "cisa_certification_claimed": False,
        "program_complete_81": program_complete_81,
        "findings_not_closed_exact": not_closed,
        "honesty": "§8.1 requires status CLOSED exactly; CLOSED_REPO/CLOSED_PARTIAL/OPEN_* do not satisfy program complete.",
    }
    print(json.dumps(report, indent=2))
    if program_complete_81:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
