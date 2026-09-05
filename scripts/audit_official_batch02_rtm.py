#!/usr/bin/env python3
"""Live RTM audit for official Batch 02 (IDs 51–100)."""

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
OVERLAP_BATCH01 = frozenset({55, 56, 59, 60})


async def _audit_one(capability_id: int) -> dict:
    from cap646.batch02_dedicated import EXPECTED_SURFACE
    from cap646.batch01_dedicated import EXPECTED_SURFACE as BATCH01_SURFACES
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
    expected = EXPECTED_SURFACE.get(capability_id) or BATCH01_SURFACES.get(capability_id)
    generic = surface in GENERIC_SURFACES and (expected is None or surface != expected)
    spine = result.get("production_spine") or ""
    expected_spine = "batch01" if capability_id in OVERLAP_BATCH01 else "batch02"
    aligned = (
        bool(result.get("success"))
        and spine == expected_spine
        and not generic
        and not exc
        and (expected is None or surface == expected)
    )
    if capability_id in OVERLAP_BATCH01:
        classification = "OVERLAP_BATCH01"
        status = "PRODUCTION-ALIGNED" if aligned else "NOT_COMPLETE"
    else:
        classification = "PRODUCTION-ALIGNED" if aligned else "NOT_COMPLETE"
        status = classification

    notes: list[str] = []
    if capability_id in OVERLAP_BATCH01:
        notes.append("legacy_batch01_extension; official_batch=batch02")
    if generic:
        notes.append(f"generic_surface:{surface}")
    if exc:
        notes.append(f"runtime_exception:{exc}")
    if spine != expected_spine:
        notes.append(f"missing_production_spine:expected={expected_spine},got={spine or 'none'}")
    if expected and surface != expected:
        notes.append(f"surface_mismatch:expected={expected},got={surface}")
    if not result.get("success"):
        notes.append("success=false")

    return {
        "id": capability_id,
        "capability": row.get("capability"),
        "official_batch": "batch02",
        "status": status,
        "classification": classification,
        "production_spine": spine or None,
        "backend": f"{result.get('backend_module')}.{result.get('backend_entrypoint')}",
        "surface": surface,
        "expected_surface": expected,
        "generic": generic,
        "exception": bool(exc),
        "notes": "; ".join(notes) if notes else None,
    }


async def main() -> None:
    from cap646.batch02_production import OFFICIAL_BATCH02_IDS

    rows = [await _audit_one(cid) for cid in sorted(OFFICIAL_BATCH02_IDS)]
    aligned = [r for r in rows if r["status"] == "PRODUCTION-ALIGNED"]
    overlap = [r for r in rows if r["classification"] == "OVERLAP_BATCH01"]
    independent = [r for r in aligned if r["classification"] == "PRODUCTION-ALIGNED" and r["id"] not in OVERLAP_BATCH01]

    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "official_batch": "batch02",
        "scope": "IDs 51–100",
        "total": len(rows),
        "production_aligned": len(aligned),
        "independent_production_aligned": len(independent),
        "overlap_batch01": len(overlap),
        "not_complete": len(rows) - len(aligned),
        "all_verified": len(aligned) == len(rows),
        "per_id": {str(r["id"]): r for r in rows},
    }
    json_path = ROOT / "docs/BATCH02_OFFICIAL_RTM_51_100.json"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "production_aligned": out["production_aligned"]}, indent=2))
    print(f"Wrote {json_path}")
    if not out["all_verified"]:
        failed = [r["id"] for r in rows if r["status"] != "PRODUCTION-ALIGNED"]
        raise SystemExit(f"batch02 RTM audit failed for: {failed}")


if __name__ == "__main__":
    asyncio.run(main())
