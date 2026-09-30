#!/usr/bin/env python3
"""FINDING-19 — record WAF/CDN verification attempt (E-OPS; honest pass/fail)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "governance/launch57/evidence/FINDING-19"


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_edge_waf_cdn.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"WAF_CDN_RUN_{stamp}.json"
    record = {
        "kind": "finding_19_waf_cdn_run",
        "program_ref": "§6 FINDING-19; L57-P7-WP4",
        "evidence_class": "E-OPS",
        "recorded_at": datetime.now(UTC).isoformat(),
        "verify_exit_code": proc.returncode,
        "verify_pass": proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-6000:],
        "stderr_tail": (proc.stderr or "")[-3000:],
        "honesty": {"index_auto_close": False, "cisa_certification_claimed": False},
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return proc.returncode if proc.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
