#!/usr/bin/env python3
"""Daily retention & deletion policy job — Sprint 0 compliance cron.

Usage:
  python scripts/run_retention_deletion_job.py

Schedule via cron / Railway scheduler — runs tier enforcement + pending hard deletes.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def main() -> int:
    from data_retention_governance import run_retention_deletion_job

    result = await run_retention_deletion_job()
    completed = len(result.get("pending_deletions", {}).get("completed", []))
    blocked = len(result.get("pending_deletions", {}).get("blocked", []))
    print(f"OK retention_job completed_deletions={completed} blocked={blocked}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
