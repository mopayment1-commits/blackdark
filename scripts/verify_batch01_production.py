#!/usr/bin/env python3
"""Live production-path proof for Batch 01 (826-completion, 50 capabilities)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch01_production import BATCH01_IDS, batch01_entrypoint


async def _prove_one(capability_id: int) -> dict:
    from cap646.backend_registry import binding_for
    from cap646.catalog import catalog_by_id
    from cap646.runtime import execute_capability

    binding = binding_for(capability_id)
    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "email": "batch01-proof@blackdark.local",
        },
    )
    row = catalog_by_id().get(capability_id, {})
    return {
        "capability_id": capability_id,
        "catalog_name": row.get("capability"),
        "track": row.get("track"),
        "production_path": (
            f"cap646.runtime.execute_capability -> cap646.batch01_production.{batch01_entrypoint(capability_id)}"
        ),
        "backend_registry": binding,
        "live_result": {
            "success": result.get("success"),
            "surface": result.get("surface"),
            "backend_module": result.get("backend_module"),
            "backend_entrypoint": result.get("backend_entrypoint"),
            "binding_source": result.get("binding_source"),
            "production_spine": result.get("production_spine"),
            "classification": result.get("classification"),
        },
        "option_a_verified": (
            binding.get("binding_source") == "explicit_option_a"
            and bool(result.get("success"))
            and result.get("production_spine") == "batch01"
            and result.get("backend_entrypoint") == batch01_entrypoint(capability_id)
        ),
    }


async def main() -> None:
    proofs = [await _prove_one(cid) for cid in sorted(BATCH01_IDS)]
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "batch": "batch01_826_completion",
        "scope": "IDs 1-59 (50 capabilities)",
        "production_runtime_path": "api/routers/cap646.py -> cap978.unified -> cap646.runtime.execute_capability -> cap646.batch01_production",
        "capability_ids": sorted(BATCH01_IDS),
        "all_verified": all(p["option_a_verified"] for p in proofs),
        "proofs": proofs,
    }
    json_path = ROOT / "docs/BATCH01_PRODUCTION_PROOF.json"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "count": len(proofs)}, indent=2))
    print(f"Wrote {json_path}")
    if not out["all_verified"]:
        failed = [p["capability_id"] for p in proofs if not p["option_a_verified"]]
        raise SystemExit(f"batch01 proof failed for: {failed}")


if __name__ == "__main__":
    asyncio.run(main())
