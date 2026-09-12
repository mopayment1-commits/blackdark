#!/usr/bin/env python3
"""Full engineering audit — 826 capabilities with v6 triple classification.

Type A = buildable NOT_COMPLETE (must reach 0 before pre-launch).
Outputs ENGINEERING_AUDIT_826_REPORT.json with per-capability live evidence.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "ENGINEERING_AUDIT_826_REPORT.json"
SUMMARY = ROOT / "ENGINEERING_AUDIT_826_SUMMARY.json"


def _triple_classify(cap_id: int, functional: dict, runtime: dict) -> dict:
    verdict = functional.get("verdict", "UNKNOWN")
    rescue = runtime.get("rescue_tier")
    external = verdict == "EXTERNAL_BLOCKED"
    duplicate = verdict == "CANONICALLY_COVERED"

    if external:
        engineering = "EXTERNAL_BLOCKED"
        gap_type = "EXTERNAL"
    elif duplicate:
        engineering = "CANONICALLY_COVERED"
        gap_type = "DEDUP"
    elif verdict == "VERIFIED_COMPLETE" and not rescue:
        engineering = "PASS_ENGINEERING"
        gap_type = "NONE"
    elif verdict == "FUNCTIONALLY_INCOMPLETE" or rescue:
        engineering = "NOT_COMPLETE"
        gap_type = "A" if not rescue else "A_RESCUE"
    else:
        engineering = "PARTIAL"
        gap_type = "B"

    evidence_class = runtime.get("evidence_class") or runtime.get("classification")
    return {
        "capability_id": cap_id,
        "engineering_status": engineering,
        "evidence_class": evidence_class,
        "live_status": "PASS_LIVE_NOT_CLAIMED",
        "gap_type": gap_type,
        "functional_verdict": verdict,
        "runtime_success": bool(runtime.get("success")),
        "rescue_tier": rescue,
        "binding_source": runtime.get("binding_source"),
        "production_spine": runtime.get("production_spine"),
        "backend_module": runtime.get("backend_module"),
        "surface": runtime.get("surface"),
        "failure_reason": functional.get("failure_reason"),
        "checks": functional.get("checks"),
        "evidence_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


async def _audit_one(cap_id: int) -> dict:
    from cap646.functional_dod import verify_functional
    from cap646.runtime import execute_capability

    try:
        runtime = await execute_capability(cap_id, params={"symbol": "BTC"}, skip_entitlement=True)
    except Exception as exc:  # noqa: BLE001
        runtime = {"success": False, "error": str(exc), "capability_id": cap_id}
    functional = await verify_functional(cap_id)
    classified = _triple_classify(cap_id, functional, runtime)
    classified["functional_checks"] = functional.get("checks")
    classified["runtime_error"] = runtime.get("error")
    return classified


async def _audit_all(concurrency: int = 4) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)

    async def _guarded(cid: int) -> dict:
        async with sem:
            try:
                return await _audit_one(cid)
            except Exception as exc:  # noqa: BLE001
                return {
                    "capability_id": cid,
                    "engineering_status": "NOT_COMPLETE",
                    "evidence_class": None,
                    "live_status": "PASS_LIVE_NOT_CLAIMED",
                    "gap_type": "A",
                    "functional_verdict": "ERROR",
                    "runtime_success": False,
                    "error": str(exc),
                    "evidence_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                }

    return await asyncio.gather(*[_guarded(i) for i in range(1, 827)])


def _batch_summary(rows: list[dict]) -> dict:
    batches: dict[str, dict] = {}
    for row in rows:
        cid = row["capability_id"]
        from cap646.batch_constants import official_batch_name

        batch = official_batch_name(cid)
        b = batches.setdefault(batch, {"type_a": 0, "pass_engineering": 0, "total": 0})
        b["total"] += 1
        if row.get("gap_type", "").startswith("A"):
            b["type_a"] += 1
        if row.get("engineering_status") == "PASS_ENGINEERING":
            b["pass_engineering"] += 1
    return batches


async def main() -> int:
    rows = await _audit_all()
    type_a = sum(1 for r in rows if r.get("gap_type", "").startswith("A"))
    pass_eng = sum(1 for r in rows if r.get("engineering_status") == "PASS_ENGINEERING")
    canon_cov = sum(1 for r in rows if r.get("engineering_status") == "CANONICALLY_COVERED")
    external_blk = sum(1 for r in rows if r.get("engineering_status") == "EXTERNAL_BLOCKED")
    partial = sum(1 for r in rows if r.get("engineering_status") == "PARTIAL")
    batches = _batch_summary(rows)
    engineering_closed = pass_eng + canon_cov + external_blk

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_capabilities": len(rows),
        "type_a_buildable_gaps": type_a,
        "pass_engineering_count": pass_eng,
        "canonically_covered_count": canon_cov,
        "external_blocked_count": external_blk,
        "partial_count": partial,
        "engineering_closure_count": engineering_closed,
        "engineering_closure_pct": round(engineering_closed / len(rows) * 100, 2) if rows else 0,
        "type_a_zero": type_a == 0,
        "all_batches_type_a_zero": all(b["type_a"] == 0 for b in batches.values()),
        "batch_summaries": batches,
        "capabilities": rows,
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "generated_at": report["generated_at"],
        "type_a_buildable_gaps": type_a,
        "pass_engineering_count": pass_eng,
        "canonically_covered_count": canon_cov,
        "external_blocked_count": external_blk,
        "engineering_closure_count": engineering_closed,
        "type_a_zero": type_a == 0,
        "batches_with_type_a": [k for k, v in batches.items() if v["type_a"] > 0],
        "PASS_LIVE_NOT_CLAIMED": True,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if type_a == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
