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
    report = run_sync_report(probe_production=probe)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    overall = report.get("overall_verdict")
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
