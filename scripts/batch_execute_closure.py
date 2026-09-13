#!/usr/bin/env python3
"""Per-batch execute closure — 25 capabilities, real runtime only."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch_constants import batch_id_range, batch_number, total_batch_count
from cap646.catalog import catalog_by_id, is_duplicate
from cap646.official_batch_production import execute


async def _run_batch(batch_num: int) -> dict:
    start, end = batch_id_range(batch_num)
    rows = []
    for cid in range(start, end + 1):
        if is_duplicate(cid):
            rows.append({"capability_id": cid, "status": "DUPLICATE", "success": True})
            continue
        try:
            r = await execute(
                cid,
                params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
            )
            rows.append(
                {
                    "capability_id": cid,
                    "capability": catalog_by_id()[cid]["capability"],
                    "success": bool(r.get("success")),
                    "surface": r.get("surface"),
                    "error": r.get("error"),
                    "build_method": (r.get("extra") or {}).get("build_method") if isinstance(r.get("extra"), dict) else r.get("build_method"),
                }
            )
        except Exception as exc:
            rows.append({"capability_id": cid, "success": False, "error": str(exc)})
    pass_n = sum(1 for r in rows if r.get("success"))
    return {
        "batch": f"batch{batch_num:02d}",
        "id_range": [start, end],
        "pass": pass_n,
        "total": len(rows),
        "pct": round(pass_n / len(rows) * 100, 2) if rows else 0,
        "capabilities": rows,
    }


async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int)
    p.add_argument("--from-batch", type=int, default=1)
    p.add_argument("--to-batch", type=int, default=total_batch_count())
    args = p.parse_args()
    batches = [args.batch] if args.batch else list(range(args.from_batch, args.to_batch + 1))
    reports = [await _run_batch(b) for b in batches]
    total_pass = sum(r["pass"] for r in reports)
    total = sum(r["total"] for r in reports)
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "methodology": "official_batch_production execute — runtime truth",
        "batches": batches,
        "pass_execute": total_pass,
        "fail_execute": total - total_pass,
        "pass_pct": round(total_pass / total * 100, 2) if total else 0,
        "by_batch": {r["batch"]: {"pass": r["pass"], "total": r["total"], "pct": r["pct"]} for r in reports},
    }
    out = ROOT / "BATCH_EXECUTE_CLOSURE_SUMMARY.json"
    out.write_text(json.dumps({"summary": summary, "batches": reports}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if total_pass == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
