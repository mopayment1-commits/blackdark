#!/usr/bin/env python3
"""FINDING-18 — record pentest attestation check (E-OPS attempt; honest pass/fail)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "governance/launch57/evidence/FINDING-18"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from pentest_attestation import verify_pentest_attestation

    verified = bool(verify_pentest_attestation())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"PENTEST_ASSURANCE_RUN_{stamp}.json"
    record = {
        "kind": "finding_18_pentest_assurance_run",
        "program_ref": "§6 FINDING-18; L57-P7-WP3",
        "evidence_class": "E-OPS",
        "recorded_at": datetime.now(UTC).isoformat(),
        "verify_pentest_attestation": verified,
        "honesty": {
            "not_cisa_certification": True,
            "index_auto_close": False,
            "transition": "scripts/transition_launch57_finding_status.py --finding FINDING-18 --apply",
        },
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps({"verify_pentest_attestation": verified}, indent=2))
    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
