#!/usr/bin/env python3
"""Record Launch-57 ops closure gate output (honest ops log — not a pentest)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "governance" / "launch57" / "evidence" / "ops_attestations"


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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fail-on-blockers",
        action="store_true",
        help="Exit 2 when ops gate reports blockers (default: exit 0 after recording)",
    )
    args = parser.parse_args()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "launch57_ops_closure_gate.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    matrix: dict | None = None
    try:
        matrix = json.loads(proc.stdout)
    except json.JSONDecodeError:
        matrix = {"raw_stdout": proc.stdout}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"OPS_ATTESTATION_{stamp}.json"
    record = {
        "kind": "launch57_ops_gate_attestation",
        "honesty": {
            "not_independent_pentest": True,
            "not_cisa_certification": True,
            "description": "Operator record of launch57_ops_closure_gate.py — blockers may remain",
        },
        "recorded_at": datetime.now(UTC).isoformat(),
        "operator": (os.getenv("LAUNCH57_OPS_OPERATOR") or "").strip() or None,
        "git_head": _git_head(),
        "launch57_prod_url": (os.getenv("LAUNCH57_PROD_URL") or "").strip() or None,
        "gate_exit_code": proc.returncode,
        "gate_pass": proc.returncode == 0,
        "matrix": matrix,
        "gate_stderr": proc.stderr[-12000:] if proc.stderr else "",
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps({"gate_pass": record["gate_pass"], "exit_code": proc.returncode}, indent=2))
    if args.fail_on_blockers and proc.returncode != 0:
        return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
