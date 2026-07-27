#!/usr/bin/env python3
"""Buyer due-diligence verification — uptime, latency, profit/fee coverage."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    from due_diligence import due_diligence_report

    report = due_diligence_report()
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
