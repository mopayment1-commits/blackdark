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


def _non_negative_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value if value >= 0 else 0
    return 0


def _scan_aggregate_metrics(report: object) -> tuple[bool, int, int, int]:
    """Scalars only — never forwards finding payloads to stdout."""
    if not isinstance(report, dict):
        return False, 0, 0, 0
    clean = report.get("clean") is True
    files_scanned = _non_negative_int(report.get("files_scanned"))
    pan_finding_count = _non_negative_int(report.get("pan_finding_count"))
    secret_finding_count = _non_negative_int(report.get("secret_finding_count"))
    return clean, files_scanned, pan_finding_count, secret_finding_count


def _emit_fds_scan_status(
    *,
    clean: bool,
    files_scanned: int,
    pan_finding_count: int,
    secret_finding_count: int,
) -> None:
    status = "clean" if clean else "dirty"
    sys.stdout.write(
        "fds_financial_data_scan "
        f"status={status} "
        f"files_scanned={files_scanned} "
        f"pan_finding_count={pan_finding_count} "
        f"secret_finding_count={secret_finding_count}\n"
    )


def main() -> int:
    report = scan_repository()
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    clean, files_scanned, pan_finding_count, secret_finding_count = _scan_aggregate_metrics(report)
    _emit_fds_scan_status(
        clean=clean,
        files_scanned=files_scanned,
        pan_finding_count=pan_finding_count,
        secret_finding_count=secret_finding_count,
    )
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
