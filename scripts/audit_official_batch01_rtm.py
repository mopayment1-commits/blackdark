#!/usr/bin/env python3
"""Live RTM audit for official Batch 01 (IDs 1–50 only)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts"}
)


async def _audit_one(capability_id: int) -> dict:
    from cap646.batch01_dedicated import EXPECTED_SURFACE
    from cap646.catalog import catalog_by_id
    from cap646.runtime import execute_capability

    row = catalog_by_id().get(capability_id, {})
    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "email": "rtm-audit@blackdark.local",
            "tier": "pro",
        },
    )
    surface = str(result.get("surface") or "")
    exc = result.get("oracle_fallback_error") or result.get("error")
    expected = EXPECTED_SURFACE.get(capability_id)
    generic = surface in GENERIC_SURFACES and (expected is None or surface != expected)
    spine = result.get("production_spine") or ""
    aligned = (
        bool(result.get("success"))
        and spine == "batch01"
        and not generic
        and not exc
        and (expected is None or surface == expected)
    )
    status = "PRODUCTION-ALIGNED" if aligned else "NOT_COMPLETE"
    notes: list[str] = []
    if generic:
        notes.append(f"generic_surface:{surface}")
    if exc:
        notes.append(f"runtime_exception:{exc}")
    if spine != "batch01":
        notes.append(f"missing_production_spine:got={spine or 'none'}")
    if expected and surface != expected:
        notes.append(f"surface_mismatch:expected={expected},got={surface}")
    if not result.get("success"):
        notes.append("success=false")

    return {
        "id": capability_id,
        "capability": row.get("capability"),
        "official_batch": "batch01",
        "status": status,
        "production_spine": spine or None,
        "backend": f"{result.get('backend_module')}.{result.get('backend_entrypoint')}",
        "surface": surface,
        "expected_surface": expected,
        "generic": generic,
        "exception": bool(exc),
        "notes": "; ".join(notes) if notes else None,
    }


async def main() -> None:
    from cap646.batch01_production import OFFICIAL_BATCH01_IDS

    rows = [await _audit_one(cid) for cid in sorted(OFFICIAL_BATCH01_IDS)]
    aligned = [r for r in rows if r["status"] == "PRODUCTION-ALIGNED"]
    not_complete = [r for r in rows if r["status"] != "PRODUCTION-ALIGNED"]
    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Official Batch 01 — IDs 1–50",
        "official_batch_baseline": "1–50 → batch01, 51–100 → batch02, 101–150 → batch03",
        "summary": {
            "total": len(rows),
            "production_aligned": len(aligned),
            "not_complete": len(not_complete),
        },
        "per_id": {str(r["id"]): r for r in rows},
        "not_complete_ids": [r["id"] for r in not_complete],
    }
    json_path = ROOT / "docs/BATCH01_OFFICIAL_RTM_1_50.json"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print(f"Wrote {json_path}")
    if not_complete:
        print("NOT_COMPLETE:", not_complete)


if __name__ == "__main__":
    asyncio.run(main())
