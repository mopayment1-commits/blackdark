#!/usr/bin/env python3
"""Entitlement gateway proof — batch03, 10 test cases (range 101-150 only)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CASES = [
    (101, {"tier": "pro"}, "pro_ai_analyst"),
    (103, {"tier": "elite"}, "overlap_batch01_api_platform"),
    (106, {"tier": "pro"}, "reused_link_provenance"),
    (110, {"tier": "pro"}, "reused_link_cross_domain"),
    (115, {"tier": "free"}, "free_screener"),
    (125, {"tier": "pro"}, "reused_link_open_interest"),
    (125, {"tier": "free"}, "pro_gated_free_denied"),
    (129, {"tier": "pro"}, "overlap_batch01_sentiment"),
    (138, {"tier": "pro"}, "pro_unlock_calendar"),
    (150, {"tier": "pro"}, "pro_protocol_kpi"),
]


async def _prove(capability_id: int, *, user: dict | None, label: str) -> dict:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(capability_id, user=user, params={"symbol": "BTC", "tier": (user or {}).get("tier")})
    gateway = result.get("gateway")
    ent = result.get("entitlement") or {}
    if isinstance(gateway, dict):
        ent = gateway.get("entitlement") or ent
    return {
        "capability_id": capability_id,
        "user_label": label,
        "user": user,
        "path": "cap646.institutional_gateway.gateway_execute",
        "skip_entitlement_used": "skip_entitlement" in str(result),
        "entitlement_allowed": ent.get("allowed"),
        "entitlement_reason": ent.get("reason") or result.get("error"),
        "success": result.get("success"),
        "surface": result.get("surface"),
        "production_spine": result.get("production_spine"),
        "catalog_link": result.get("catalog_link"),
    }


async def main() -> None:
    proofs = [await _prove(cid, user=user, label=label) for cid, user, label in CASES]
    by = {p["user_label"]: p for p in proofs}
    checks = {
        "no_skip_entitlement": all(not p["skip_entitlement_used"] for p in proofs),
        "count_10": len(proofs) == 10,
        "125_free_denied": by["pro_gated_free_denied"]["entitlement_allowed"] is False,
        "125_pro_allowed": by["reused_link_open_interest"]["entitlement_allowed"] is True,
        "103_overlap_batch01": by["overlap_batch01_api_platform"]["production_spine"] == "batch01",
        "106_reused_link": (by["reused_link_provenance"].get("catalog_link") or {}).get("duplicate_of") == 63,
    }
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "Batch03 entitlement gateway — 10 test cases (range 101-150)",
        "unique_capability_ids": sorted({p["capability_id"] for p in proofs}),
        "test_case_count": len(proofs),
        "script": "scripts/verify_entitlement_batch03_gateway_proof.py",
        "proofs": proofs,
        "checks": checks,
        "all_verified": all(checks.values()),
    }
    path = ROOT / "docs/BATCH03_ENTITLEMENT_GATEWAY_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "checks": checks}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        raise SystemExit("Batch03 entitlement proof failed")


if __name__ == "__main__":
    asyncio.run(main())
