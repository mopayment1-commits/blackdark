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
from governance.public_report import coerce_bool, coerce_int, fds_scan_stdout_line

OUT = ROOT / "FDS_FINANCIAL_DATA_SCAN_REPORT.json"


def main() -> int:
    report = scan_repository()
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    clean = coerce_bool(report.get("clean"))
    files_scanned = coerce_int(report.get("files_scanned"))
    pan_finding_count = coerce_int(report.get("pan_finding_count"))
    secret_finding_count = coerce_int(report.get("secret_finding_count"))
    print(
        fds_scan_stdout_line(
            clean=clean,
            files_scanned=files_scanned,
            pan_finding_count=pan_finding_count,
            secret_finding_count=secret_finding_count,
        )
    )
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
