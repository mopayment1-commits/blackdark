#!/usr/bin/env python3
"""Run full RVM verification and validation; emit RVM.json + RVM_SUMMARY.json."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rvm.run import run_rvm


async def main() -> int:
    result = await run_rvm()
    summary = result["summary"]
    print(json.dumps(summary, indent=2))
    return 0 if summary["fail_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
