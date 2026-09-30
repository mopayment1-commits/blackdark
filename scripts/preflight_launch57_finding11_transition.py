#!/usr/bin/env python3
"""Dry-run FINDING-11 transition only (program §6)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSITION = ROOT / "scripts/transition_launch57_finding_status.py"


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(TRANSITION), "--finding", "FINDING-11"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report = {
        "finding": "FINDING-11",
        "mode": "dry_run_only",
        "apply_used": False,
        "exit_code": proc.returncode,
        "dry_run_pass": proc.returncode == 0,
        "cisa_certification_claimed": False,
        "stdout_tail": (proc.stdout or "").strip()[-500:],
        "stderr_tail": (proc.stderr or "").strip()[-500:],
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
