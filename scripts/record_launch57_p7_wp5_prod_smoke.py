#!/usr/bin/env python3
"""Record L57-P7-WP5 production smoke output as E-RUN (does not close findings)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "governance/launch57/evidence/P7_WP5"


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def main() -> int:
    if not (os.getenv("LAUNCH57_PROD_URL") or "").strip():
        print("LAUNCH57_PROD_URL required", file=sys.stderr)
        return 3
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_launch57_p7_wp5_production_smoke.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"P7_WP5_PROD_SMOKE_{stamp}.json"
    matrix: dict | None = None
    try:
        matrix = json.loads(proc.stdout)
    except json.JSONDecodeError:
        matrix = {"raw_stdout": proc.stdout}
    record = {
        "kind": "launch57_p7_wp5_production_smoke",
        "evidence_class": "E-RUN",
        "recorded_at": datetime.now(UTC).isoformat(),
        "git_head": _git_head(),
        "exit_code": proc.returncode,
        "pass": proc.returncode == 0,
        "matrix": matrix,
        "stderr_tail": (proc.stderr or "")[-4000:],
        "honesty": {"not_program_closure": True, "cisa_certification_claimed": False},
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return proc.returncode if proc.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
