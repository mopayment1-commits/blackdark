#!/usr/bin/env python3
"""FDS-05 / FDS-18 repository PAN + secret scan. Exit non-zero on prohibited finding."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from financial_data.scanner import scan_repository

OUT = ROOT / "FDS_FINANCIAL_DATA_SCAN_REPORT.json"


def main() -> int:
    report = scan_repository()
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = {
        "clean": report.get("clean"),
        "files_scanned": report.get("files_scanned"),
        "pan_finding_count": report.get("pan_finding_count"),
        "secret_finding_count": report.get("secret_finding_count"),
    }
    print(json.dumps(summary, indent=2))
    return 0 if report.get("clean") else 1


if __name__ == "__main__":
    raise SystemExit(main())
