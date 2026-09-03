#!/usr/bin/env python3
"""Live RTM audit for official Batch 03 (IDs 101–150)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch03_dedicated import BATCH03_OVERLAP_BATCH01_IDS, EXPECTED_SURFACE, GENERIC_SURFACES
from cap646.batch03_production import BATCH03_IDS

REUSED_LINK_IDS = frozenset({106, 107, 110, 125})
CANONICAL_FOR_REUSED = {106: 63, 107: 64, 110: 69, 125: 85}

_BINDING_FILE = "cap646/batch03_dedicated.py"


def _binding_function(capability_id: int) -> str | None:
    if capability_id in BATCH03_OVERLAP_BATCH01_IDS:
        return f"cap646.batch01_production.cap_{capability_id:03d}"
    if capability_id in REUSED_LINK_IDS:
        return f"_cap{capability_id}"
    if capability_id in EXPECTED_SURFACE:
        return f"_cap{capability_id}"
    return None


async def _audit_one(capability_id: int) -> dict:
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

    if capability_id in BATCH03_OVERLAP_BATCH01_IDS:
        expected_spine = "batch01"
        classification = "OVERLAP-PARTIAL"
    elif capability_id in REUSED_LINK_IDS:
        expected_spine = "batch03"
        classification = "REUSED-LINK"
    else:
        expected_spine = "batch03"
        classification = "PRODUCTION-ALIGNED"

    spine = result.get("production_spine") or ""
    spine_ok = spine in {expected_spine, "batch03_prep", "batch03"}
    link_ok = True
    if capability_id in REUSED_LINK_IDS:
        top_link = result.get("catalog_link") or {}
        if not top_link.get("duplicate_of"):
            payload_key = next(
                (k for k in result if isinstance(result.get(k), dict) and result[k].get("catalog_link")),
                None,
            )
            if payload_key:
                top_link = result[payload_key].get("catalog_link") or {}
        dup = top_link.get("duplicate_of")
        link_ok = dup == CANONICAL_FOR_REUSED[capability_id]

    aligned = (
        bool(result.get("success"))
        and spine_ok
        and not generic
        and not exc
        and (expected is None or surface == expected)
        and (capability_id not in REUSED_LINK_IDS or link_ok)
    )

    if capability_id in REUSED_LINK_IDS:
        status = "REUSED-LINK" if aligned else "NOT_COMPLETE"
    elif capability_id in BATCH03_OVERLAP_BATCH01_IDS:
        status = "OVERLAP-PARTIAL" if aligned else "NOT_COMPLETE"
    else:
        status = "PRODUCTION-ALIGNED" if aligned else "NOT_COMPLETE"

    notes: list[str] = []
    if capability_id in BATCH03_OVERLAP_BATCH01_IDS:
        notes.append("overlap_batch01; runtime routes batch01 before batch03")
    if capability_id in REUSED_LINK_IDS:
        notes.append(f"canonical=#{CANONICAL_FOR_REUSED[capability_id]} batch02 PRODUCTION-ALIGNED")
    if generic:
        notes.append(f"generic_surface:{surface}")
    if exc:
        notes.append(f"runtime_exception:{exc}")
    if spine not in {expected_spine, "batch03_prep", "batch03"}:
        notes.append(f"spine_mismatch:expected={expected_spine},got={spine or 'none'}")
    if expected and surface != expected:
        notes.append(f"surface_mismatch:expected={expected},got={surface}")
    if not result.get("success"):
        notes.append("success=false")
    if capability_id in REUSED_LINK_IDS and not link_ok:
        notes.append("missing_or_wrong_catalog_link.duplicate_of")

    return {
        "id": capability_id,
        "capability": row.get("capability"),
        "official_batch": "batch03",
        "status": status,
        "classification": classification,
        "production_spine": spine or None,
        "binding_file": _BINDING_FILE if capability_id not in BATCH03_OVERLAP_BATCH01_IDS else "cap646/batch01_production.py",
        "binding_function": _binding_function(capability_id),
        "backend": f"{result.get('backend_module')}.{result.get('backend_entrypoint')}",
        "surface": surface,
        "expected_surface": expected,
        "generic": generic,
        "exception": bool(exc),
        "notes": "; ".join(notes) if notes else None,
    }


async def main() -> None:
    rows = [await _audit_one(cid) for cid in sorted(BATCH03_IDS)]
    aligned = [r for r in rows if r["status"] == "PRODUCTION-ALIGNED"]
    reused = [r for r in rows if r["status"] == "REUSED-LINK"]
    overlap = [r for r in rows if r["status"] == "OVERLAP-PARTIAL"]
    not_complete = [r for r in rows if r["status"] == "NOT_COMPLETE"]
    independent = [r for r in aligned if r["classification"] == "PRODUCTION-ALIGNED"]

    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "official_batch": "batch03",
        "scope": "IDs 101–150",
        "total": len(rows),
        "production_aligned": len(aligned),
        "independent_production_aligned": len(independent),
        "reused_link": len(reused),
        "overlap_partial": len(overlap),
        "not_complete": len(not_complete),
        "all_verified": len(not_complete) == 0,
        "per_id": {str(r["id"]): r for r in rows},
    }
    path = ROOT / "docs/BATCH03_OFFICIAL_RTM_101_150.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("official_batch", "total", "production_aligned", "reused_link", "overlap_partial", "not_complete", "all_verified")}, indent=2))
    print(f"Wrote {path}")
    if not_complete:
        print("NOT_COMPLETE:", [r["id"] for r in not_complete])
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
