#!/usr/bin/env python3
"""Record §8.3 V-4 Legal review ID (E-LEGAL signoff log — does not close findings)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "governance/launch57/evidence/legal_review_signoffs"


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
    parser.add_argument("--review-id", required=True, help="Legal review ticket / memo ID")
    parser.add_argument("--reviewer-role", default="Legal")
    args = parser.parse_args()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_launch57_legal_v4_bundle.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**dict(__import__("os").environ), "LAUNCH57_LEGAL_REVIEW_ID": args.review_id.strip()},
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"LEGAL_V4_SIGNOFF_{stamp}.json"
    record = {
        "kind": "launch57_legal_v4_signoff",
        "program_section": "§8.3 V-4",
        "evidence_class": "E-LEGAL",
        "review_id": args.review_id.strip(),
        "reviewer_role": args.reviewer_role.strip(),
        "recorded_at": datetime.now(UTC).isoformat(),
        "git_head": _git_head(),
        "bundle_verify_exit_code": proc.returncode,
        "honesty": {"cisa_certification_claimed": False, "not_finding_closure": True},
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0 if proc.returncode == 0 else proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
