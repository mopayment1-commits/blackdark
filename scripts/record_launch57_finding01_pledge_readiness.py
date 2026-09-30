#!/usr/bin/env python3
"""FINDING-01 — record executive pledge readiness check (E-LEGAL prep; not signed pledge)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "governance/launch57/evidence/FINDING-01"
REQUIRED = (
    "docs/governance/SECURE_BY_DESIGN_PLEDGE_STATUS.md",
    "docs/governance/SECURE_BY_DESIGN_PLEDGE_SUBMISSION_PACKAGE.md",
    "docs/governance/SECURE_BY_DESIGN_PLEDGE_EXECUTION_CHECKLIST.md",
)


def main() -> int:
    missing = [rel for rel in REQUIRED if not (ROOT / rel).is_file()]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"PLEDGE_READINESS_{stamp}.json"
    record = {
        "kind": "finding_01_pledge_readiness",
        "program_ref": "§6 FINDING-01; L57-P6-WP1",
        "evidence_class": "E-LEGAL",
        "recorded_at": datetime.now(UTC).isoformat(),
        "artifacts_present": not missing,
        "missing": missing,
        "pledge_submitted": False,
        "honesty": {
            "not_cisa_pledge_claim": True,
            "next": "record_pledge_submission.py --pledge-url ... --apply",
        },
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
