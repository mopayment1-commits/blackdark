#!/usr/bin/env python3
"""Batch-by-batch from-scratch closure report (v6 deepest meaning, 25 caps/batch)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch_constants import CAPABILITIES_PER_BATCH, TOTAL_CAPABILITIES, batch_id_range, total_batch_count
from cap646.v6_from_scratch_dod import verify_from_scratch


async def _audit_batch(batch_num: int) -> dict:
    start, end = batch_id_range(batch_num)
    results = []
    for cid in range(start, end + 1):
        results.append(await verify_from_scratch(cid))
    pass_n = sum(1 for r in results if r["PASS_FROM_SCRATCH"])
    total = len(results)
    return {
        "batch": f"batch{batch_num:02d}",
        "batch_number": batch_num,
        "id_range": [start, end],
        "pass_from_scratch": pass_n,
        "total": total,
        "pass_pct": round(pass_n / total * 100, 2) if total else 0.0,
        "capabilities": results,
    }


async def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="From-scratch batch closure (v6)")
    p.add_argument("--batch", type=int, help="Single batch number (1-34)")
    p.add_argument("--from-batch", type=int, default=1)
    p.add_argument("--to-batch", type=int, default=total_batch_count())
    args = p.parse_args()

    if args.batch:
        batches = [args.batch]
    else:
        batches = list(range(args.from_batch, args.to_batch + 1))

    batch_reports = [await _audit_batch(b) for b in batches]
    total_pass = sum(b["pass_from_scratch"] for b in batch_reports)
    total_caps = sum(b["total"] for b in batch_reports)

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "standard": "BLACKDARK Institutional Capability Standard 2026 v6 — from-scratch",
        "capabilities_per_batch": CAPABILITIES_PER_BATCH,
        "total_capabilities": TOTAL_CAPABILITIES,
        "scope_batches": batches,
        "pass_from_scratch": total_pass,
        "not_from_scratch": total_caps - total_pass,
        "pass_pct": round(total_pass / total_caps * 100, 2) if total_caps else 0.0,
        "by_batch": {b["batch"]: {"pass": b["pass_from_scratch"], "total": b["total"], "pct": b["pass_pct"]} for b in batch_reports},
    }

    out_summary = ROOT / "FROM_SCRATCH_BATCH_CLOSURE_SUMMARY.json"
    out_report = ROOT / "FROM_SCRATCH_BATCH_CLOSURE_REPORT.json"
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    out_report.write_text(json.dumps({"summary": summary, "batches": batch_reports}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
