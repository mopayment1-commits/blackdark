#!/usr/bin/env python3
"""Backfill oracle audit chain from existing database predictions."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main() -> int:
    from database import init_db
    from oracle_track_record import backfill_from_database, public_track_record

    await init_db()
    print("Backfilling oracle track record from database...")
    result = await backfill_from_database()
    print(f"  created events: {result['backfilled_created']}")
    print(f"  resolved events: {result['backfilled_resolved']}")
    print(f"  chain records:   {result['chain_records']}")
    print(f"  integrity valid: {result['integrity_valid']}")

    stats = public_track_record()
    cum = stats.get("cumulative") or {}
    print(f"\nCumulative hit rate: {cum.get('hit_rate_percent')}%")
    print(f"Resolved: {cum.get('resolved_predictions')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
