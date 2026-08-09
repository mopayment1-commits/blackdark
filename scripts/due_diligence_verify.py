#!/usr/bin/env python3
"""Buyer due-diligence verification — uptime, latency, profit/fee coverage."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    parser = argparse.ArgumentParser(description="BLACKDARK due-diligence verify")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI smoke: require latency+coverage+HA; uptime probes optional (no history yet)",
    )
    args = parser.parse_args()

    from due_diligence import due_diligence_report

    report = due_diligence_report()
    print(json.dumps(report, indent=2, ensure_ascii=True))

    if report.get("status") == "pass":
        return 0

    if args.ci:
        checks = report.get("checks") or {}
        required = (
            "latency_p99_le_50ms",
            "profit_fee_coverage_ge_90",
            "ha_architecture_ready",
        )
        if all(checks.get(k) for k in required):
            # Uptime SLA needs a live probe history — not available on fresh CI runners.
            return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
