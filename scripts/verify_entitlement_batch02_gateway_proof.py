#!/usr/bin/env python3
"""Expanded entitlement gateway proof — batch02, 10 IDs across tiers."""

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
    (51, {"tier": "free"}, "free_macro"),
    (53, {"tier": "free"}, "free_btc_macro"),
    (55, {"tier": "pro"}, "overlap_batch01_nvt"),
    (56, {"tier": "pro"}, "overlap_batch01_screener"),
    (59, {"tier": "pro"}, "overlap_batch01_dashboard"),
    (60, {"tier": "pro"}, "overlap_batch01_alerts"),
    (69, {"tier": "pro"}, "pro_cross_domain"),
    (85, {"tier": "pro"}, "pro_open_interest"),
    (100, {"tier": "free"}, "free_oracle_track"),
    (103, {"tier": "free"}, "out_of_scope_denied"),
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
    }


async def main() -> None:
    proofs = [await _prove(cid, user=user, label=label) for cid, user, label in CASES]
    by = {p["user_label"]: p for p in proofs}
    checks = {
        "no_skip_entitlement": all(not p["skip_entitlement_used"] for p in proofs),
        "count_10": len(proofs) == 10,
        "103_free_denied": by["out_of_scope_denied"]["entitlement_allowed"] is False,
        "55_overlap_batch01": by["overlap_batch01_nvt"]["production_spine"] == "batch01",
        "85_pro_allowed": by["pro_open_interest"]["entitlement_allowed"] is True,
    }
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "Batch02 entitlement gateway — 10 IDs",
        "script": "scripts/verify_entitlement_batch02_gateway_proof.py",
        "proofs": proofs,
        "checks": checks,
        "all_verified": all(checks.values()),
    }
    path = ROOT / "docs/BATCH02_ENTITLEMENT_GATEWAY_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "checks": checks}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        raise SystemExit("Batch02 entitlement proof failed")


if __name__ == "__main__":
    asyncio.run(main())
