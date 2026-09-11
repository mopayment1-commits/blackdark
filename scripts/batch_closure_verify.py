#!/usr/bin/env python3
"""Verify official batch closure via cap646 production path."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BATCHES = {
    "batch01": range(1, 51),
    "batch02": range(51, 101),
    "batch03": range(101, 151),
}


async def _verify_id(cap_id: int) -> dict:
    from cap646.runtime import execute_capability

    try:
        result = await execute_capability(cap_id, params={"symbol": "BTC"}, skip_entitlement=True)
        ok = bool(result.get("success"))
        return {"id": cap_id, "ok": ok, "error": result.get("error")}
    except Exception as exc:  # noqa: BLE001
        return {"id": cap_id, "ok": False, "error": str(exc)}


async def verify_batch(name: str, ids: range) -> dict:
    results = await asyncio.gather(*[_verify_id(i) for i in ids])
    ok_count = sum(1 for r in results if r["ok"])
    return {
        "batch": name,
        "total": len(results),
        "ok": ok_count,
        "fail": len(results) - ok_count,
        "failures": [r for r in results if not r["ok"]][:20],
    }


async def main() -> int:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "batches": [],
    }
    for name, ids in BATCHES.items():
        report["batches"].append(await verify_batch(name, ids))
    out = ROOT / "BATCH_CLOSURE_VERIFY_REPORT.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    all_ok = all(b["fail"] == 0 for b in report["batches"])
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
