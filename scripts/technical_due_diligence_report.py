#!/usr/bin/env python3
"""Generate Senior Technical Due Diligence report (requirements 1–20)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    from technical_due_diligence import run_sync_report

    probe = "--no-probe" not in sys.argv
    smoke = "--smoke" in sys.argv
    report = run_sync_report(probe_production=probe)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    if smoke:
        # CI smoke: report generation is the gate; buyer-strict pass is --strict.
        return 0 if isinstance(report, dict) and "overall_verdict" in report else 1
    overall = report.get("overall_verdict")
    if "--strict" in sys.argv:
        return 0 if overall == "pass" else 1
    # Default (buyer script): pass or partial with no hard FAIL budget breach still exits 1
    # unless explicitly passing — keep historical fail-closed for acquisition use.
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
