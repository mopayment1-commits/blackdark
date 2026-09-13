#!/usr/bin/env python3
"""Verify official batch closure via cap646 production path — 25-cap institutional batches."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _build_batches() -> dict[str, range]:
    from cap646.batch_constants import batch_id_range, total_batch_count

    out: dict[str, range] = {}
    for n in range(1, total_batch_count() + 1):
        start, end = batch_id_range(n)
        out[f"batch{n:02d}"] = range(start, end + 1)
    return out


BATCHES = _build_batches()


async def _verify_id(cap_id: int) -> dict:
    from cap646.runtime import execute_capability

    try:
        result = await execute_capability(cap_id, skip_entitlement=True, params={"symbol": "BTC"})
        return {"capability_id": cap_id, "success": bool(result.get("success")), "surface": result.get("surface")}
    except Exception as exc:
        return {"capability_id": cap_id, "success": False, "error": str(exc)[:200]}


async def _verify_batch(name: str, ids: range) -> dict:
    rows = await asyncio.gather(*[_verify_id(i) for i in ids])
    ok = sum(1 for r in rows if r.get("success"))
    return {"batch": name, "total": len(rows), "pass": ok, "fail": len(rows) - ok}


async def main_async() -> dict:
    results = []
    for name, ids in BATCHES.items():
        results.append(await _verify_batch(name, ids))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "capabilities_per_batch": 25,
        "batches": results,
    }


def main() -> int:
    report = asyncio.run(main_async())
    out = ROOT / "BATCH_CLOSURE_VERIFY_25CAP.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all(b["fail"] == 0 for b in report["batches"]) else 1


if __name__ == "__main__":
    sys.exit(main())
