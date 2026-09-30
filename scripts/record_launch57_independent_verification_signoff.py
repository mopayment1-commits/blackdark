#!/usr/bin/env python3
"""Record §8.3 human sign-off (gitignored) — does not set program complete or CISA claims."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json"
OUT_DIR = ROOT / "governance/launch57/evidence/independent_verification_signoffs"
VALID_STEPS = frozenset({"V-1", "V-2", "V-3", "V-4"})


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
    parser.add_argument("--step", required=True, choices=sorted(VALID_STEPS))
    parser.add_argument("--signer-role", required=True)
    parser.add_argument("--reference", default="", help="CI URL, legal review ID, or ISO8601 attestation note")
    args = parser.parse_args()
    if not REGISTER.is_file():
        print("MISSING independent verification register", file=sys.stderr)
        return 1
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    step_meta = (reg.get("steps") or {}).get(args.step)
    if not step_meta:
        print("invalid step in register", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"IV_SIGNOFF_{args.step}_{stamp}.json"
    record = {
        "kind": "launch57_independent_verification_signoff",
        "program_section": reg.get("program_section"),
        "step": args.step,
        "executor_program_role": step_meta.get("executor"),
        "signer_role": args.signer_role.strip(),
        "reference": (args.reference or "").strip() or None,
        "recorded_at": datetime.now(UTC).isoformat(),
        "git_head": _git_head(),
        "honesty": {
            "cisa_certification_claimed": False,
            "program_closure_verification_complete": False,
            "not_substitute_for_finding_closure": True,
        },
        "operator_env": (os.getenv("LAUNCH57_OPS_OPERATOR") or "").strip() or None,
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps({"step": args.step, "program_closure_verification_complete": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
