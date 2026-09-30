#!/usr/bin/env python3
"""Dry-run FINDING-18 transition (pentest attestation must verify for apply)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/transition_launch57_finding_status.py"), "--finding", "FINDING-18"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report = {
        "finding": "FINDING-18",
        "mode": "dry_run_only",
        "apply_used": False,
        "exit_code": proc.returncode,
        "dry_run_pass": proc.returncode == 0,
        "cisa_certification_claimed": False,
        "program_ref": "§6 FINDING-18",
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
