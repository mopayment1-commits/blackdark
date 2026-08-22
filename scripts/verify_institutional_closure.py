#!/usr/bin/env python3
"""Institutional closure gate — CI/DD verification for CAP978 baseline."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


async def main() -> int:
    parser = argparse.ArgumentParser(description="Verify CAP978 institutional closure gate")
    parser.add_argument("--ci", action="store_true", help="CI smoke: sample closure + artifact invariants")
    parser.add_argument("--full", action="store_true", help="Full 978 closure + baseline count lock")
    parser.add_argument("--no-artifacts", action="store_true", help="Skip committed JSON artifact checks")
    parser.add_argument(
        "--write-checklist",
        default="",
        help="Write commercial launch checklist JSON to path",
    )
    args = parser.parse_args()

    import database

    await database.init_db()

    from cap978.institutional_gate import commercial_launch_checklist, run_institutional_gate

    if args.write_checklist:
        path = Path(args.write_checklist)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(commercial_launch_checklist(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(path)}, indent=2))

    report = await run_institutional_gate(
        sample=not args.full,
        check_artifacts=not args.no_artifacts,
        include_commercial=bool(args.write_checklist) or args.full,
    )
    print(json.dumps({k: v for k, v in report.items() if k != "commercial_launch"}, indent=2, ensure_ascii=False))

    if report["verdict"] != "PASS":
        return 1
    if args.full and report.get("closure_verdict") != "VERIFIED COMPLETE":
        return 1
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(asyncio.run(main()))
