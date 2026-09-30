#!/usr/bin/env python3
"""Dry-run transition_launch57_finding_status for open ops package findings (honest readiness)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json"
TRANSITION = ROOT / "scripts/transition_launch57_finding_status.py"


def main() -> int:
    if not PKG.is_file():
        return 1
    pkg = json.loads(PKG.read_text(encoding="utf-8"))
    results: list[dict] = []
    ready: list[str] = []
    blocked: list[str] = []
    for fid in sorted((pkg.get("open_or_partial_findings") or {}).keys()):
        proc = subprocess.run(
            [sys.executable, str(TRANSITION), "--finding", fid],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        ok_dry = proc.returncode == 0
        results.append({"finding": fid, "exit_code": proc.returncode, "dry_run_pass": ok_dry})
        if ok_dry:
            ready.append(fid)
        else:
            blocked.append(fid)
    report = {
        "mode": "dry_run_only",
        "apply_used": False,
        "cisa_certification_claimed": False,
        "ready_for_apply_with_evidence": ready,
        "blocked": blocked,
        "results": results,
        "honesty": "exit 0 dry-run means verification passed; use --apply only with real E-OPS/E-LEGAL evidence",
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
