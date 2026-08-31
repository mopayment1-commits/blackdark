#!/usr/bin/env python3
"""Live production-path proof for Option A capabilities (#338, #500, #507, #534)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OPTION_A_IDS = (338, 500, 507, 534)


async def _prove_one(capability_id: int) -> dict:
    from cap646.backend_registry import binding_for
    from cap646.catalog import catalog_by_id
    from cap646.runtime import execute_capability

    binding = binding_for(capability_id)
    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC"})
    row = catalog_by_id().get(capability_id, {})
    return {
        "capability_id": capability_id,
        "catalog_name": row.get("capability"),
        "track": row.get("track"),
        "production_path": f"cap646.runtime.execute_capability -> {binding['backend_module']}.{binding['backend_entrypoint']}",
        "backend_registry": binding,
        "live_result": {
            "success": result.get("success"),
            "surface": result.get("surface"),
            "backend_module": result.get("backend_module"),
            "backend_entrypoint": result.get("backend_entrypoint"),
            "binding_source": result.get("binding_source"),
            "classification": result.get("classification"),
            "evidence_class": result.get("evidence_class"),
        },
        "option_a_verified": (
            binding.get("binding_source") == "explicit_option_a"
            and bool(result.get("success"))
            and result.get("surface") == binding.get("surface")
        ),
    }


async def main() -> None:
    proofs = [await _prove_one(cid) for cid in OPTION_A_IDS]
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "production_runtime_path": "api/routers/cap646.py -> cap978.unified -> cap646.runtime.execute_capability",
        "option_a_ids": list(OPTION_A_IDS),
        "all_verified": all(p["option_a_verified"] for p in proofs),
        "proofs": proofs,
    }
    json_path = ROOT / "docs/OPTION_A_PRODUCTION_PROOF.json"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"Wrote {json_path}")
    if not out["all_verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
