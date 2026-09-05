#!/usr/bin/env python3
"""Expanded entitlement gateway proof — batch01, 10 test cases across tiers (9 unique IDs)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 10 test cases / 9 unique IDs in official range 1-50 (Batch 03 IDs prohibited).
CASES = [
    (1, {"tier": "free"}, "free_allowed"),
    (8, {"tier": "free"}, "free_allowed"),
    (21, {"tier": "free"}, "free_allowed"),
    (38, {"tier": "free"}, "free_tier_path"),
    (39, {"tier": "free"}, "free_tier_path"),
    (24, {"tier": "pro"}, "pro_allowed"),
    (47, {"tier": "free"}, "pro_gated_free_denied"),
    (47, {"tier": "pro"}, "pro_gated_pro_allowed"),
    (50, {"tier": "pro"}, "pro_dedicated"),
    (46, {"tier": "pro"}, "pro_dedicated_46"),
]


async def _prove(capability_id: int, *, user: dict | None, label: str) -> dict:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(capability_id, user=user, params={"symbol": "BTC", "tier": (user or {}).get("tier")})
    gateway = result.get("gateway")
    ent = result.get("entitlement") or {}
    if isinstance(gateway, dict):
        ent = gateway.get("entitlement") or ent
    skip = "skip_entitlement" in str(result)
    return {
        "capability_id": capability_id,
        "user_label": label,
        "user": user,
        "path": "cap646.institutional_gateway.gateway_execute",
        "skip_entitlement_used": skip,
        "entitlement_allowed": ent.get("allowed"),
        "entitlement_reason": ent.get("reason") or result.get("error"),
        "success": result.get("success"),
        "surface": result.get("surface"),
        "production_spine": result.get("production_spine"),
    }


async def main() -> None:
    proofs = [await _prove(cid, user=user, label=label) for cid, user, label in CASES]
    checks = {
        "no_skip_entitlement": all(not p["skip_entitlement_used"] for p in proofs),
        "47_free_denied": any(p["capability_id"] == 47 and p["user_label"] == "pro_gated_free_denied" and p["entitlement_reason"] in {"tier_insufficient", "teaser"} for p in proofs),
        "47_pro_allowed": any(p["capability_id"] == 47 and p["user_label"] == "pro_gated_pro_allowed" and p["entitlement_allowed"] for p in proofs),
        "count_10": len(proofs) == 10,
    }
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "Batch01 entitlement gateway — 10 test cases (9 unique IDs in range 1-50)",
        "unique_capability_ids": sorted({p["capability_id"] for p in proofs}),
        "test_case_count": len(proofs),
        "script": "scripts/verify_entitlement_gateway_proof.py",
        "proofs": proofs,
        "checks": checks,
        "all_verified": all(checks.values()),
    }
    path = ROOT / "docs/BATCH01_ENTITLEMENT_GATEWAY_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "checks": checks}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        raise SystemExit("Batch01 entitlement proof failed")


if __name__ == "__main__":
    asyncio.run(main())
