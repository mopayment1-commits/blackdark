#!/usr/bin/env python3
"""FINDING-14 / RFC-9116 — record production security.txt verification (E-RUN), no index auto-close."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "governance/launch57/evidence/FINDING-14"


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
    prod = (os.getenv("LAUNCH57_PROD_URL") or "").strip()
    if not prod:
        print("LAUNCH57_PROD_URL required for production security.txt E-RUN", file=sys.stderr)
        return 3
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_well_known_security_txt.py"), "--url", prod],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"SECURITY_TXT_PROD_RUN_{stamp}.json"
    record = {
        "kind": "finding_14_security_txt_prod_verification",
        "program_ref": "§6 FINDING-14; RFC-9116",
        "evidence_class": "E-RUN",
        "recorded_at": datetime.now(UTC).isoformat(),
        "git_head": _git_head(),
        "prod_url": prod,
        "verify_exit_code": proc.returncode,
        "verify_pass": proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-8000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
        "honesty": {
            "does_not_auto_close_evidence_index": True,
            "use_transition_script_with_apply": "scripts/transition_launch57_finding_status.py --finding FINDING-14 --apply",
        },
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps({"verify_pass": record["verify_pass"]}, indent=2))
    return 0 if proc.returncode == 0 else proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
