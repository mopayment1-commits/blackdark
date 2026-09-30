#!/usr/bin/env python3
"""FINDING-11 — record Sec Lead SBOM gap approval (gitignored E-ART; no auto index close)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "governance/launch57/LAUNCH57_FINDING_11_SBOM_CLOSURE_LANE.json"
GAP = ROOT / "governance/launch57/LAUNCH57_NTIA_SBOM_GAP_ANALYSIS.json"
OUT_DIR = ROOT / "governance/launch57/evidence/FINDING-11"

APPROVAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")


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
    parser.add_argument("--approval-id", required=True, help="Sec Lead ticket / review id")
    parser.add_argument("--recorded-by", required=True, help="Security Lead role id")
    args = parser.parse_args()
    aid = args.approval_id.strip()
    if not APPROVAL_ID_RE.match(aid):
        print("approval-id must be 3-128 chars alphanumeric/._-", file=sys.stderr)
        return 1
    if not LANE.is_file() or not GAP.is_file():
        return 1
    lane = json.loads(LANE.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"SBOM_SEC_LEAD_APPROVAL_{stamp}.json"
    record = {
        "kind": "finding_11_sbom_sec_lead_approval",
        "program_ref": "§6 FINDING-11",
        "evidence_class": "E-ART",
        "approval_id": aid,
        "recorded_by": args.recorded_by.strip(),
        "recorded_at": datetime.now(UTC).isoformat(),
        "git_head": _git_head(),
        "gap_analysis": str(GAP.relative_to(ROOT)),
        "honesty": {
            "cisa_certification_claimed": False,
            "index_auto_close": False,
            "transition": "export LAUNCH57_SBOM_SEC_LEAD_APPROVAL_ID=<id> && "
            "python scripts/transition_launch57_finding_status.py --finding FINDING-11 --apply",
        },
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps({"lane": lane.get("finding_id"), "set_env": "LAUNCH57_SBOM_SEC_LEAD_APPROVAL_ID"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
