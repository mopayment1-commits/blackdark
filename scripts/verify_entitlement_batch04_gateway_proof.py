#!/usr/bin/env python3
"""Entitlement gateway proof — batch04, 10 test cases (range 151-200 only)."""

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
    (151, {"tier": "pro"}, "pro_quarterly_reports"),
    (159, {"tier": "elite"}, "pending_reused_elite_allowed"),
    (159, {"tier": "free"}, "canonical_103_free_denied"),
    (175, {"tier": "pro"}, "overlap_batch01_sentiment"),
    (183, {"tier": "free"}, "distinct_whale_free_allowed"),
    (189, {"tier": "pro"}, "pro_exchange_netflow"),
    (161, {"tier": "elite"}, "elite_institutional_delivery"),
    (161, {"tier": "free"}, "elite_gated_free_denied"),
    (194, {"tier": "free"}, "free_nvt_intelligence"),
    (200, {"tier": "pro"}, "pro_token_circulation"),
]


async def _prove(capability_id: int, *, user: dict | None, label: str) -> dict:
    from cap646.catalog import canonical_id
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        capability_id,
        user=user,
        params={"symbol": "BTC", "tier": (user or {}).get("tier")},
    )
    gateway = result.get("gateway")
    ent = result.get("entitlement") or {}
    if isinstance(gateway, dict):
        ent = gateway.get("entitlement") or ent
    return {
        "capability_id": capability_id,
        "canonical_id": canonical_id(capability_id),
        "user_label": label,
        "user": user,
        "path": "cap646.institutional_gateway.gateway_execute",
        "skip_entitlement_used": "skip_entitlement" in str(result),
        "entitlement_allowed": ent.get("allowed"),
        "entitlement_reason": ent.get("reason") or result.get("error"),
        "required_tier": ent.get("required_tier"),
        "success": result.get("success"),
        "surface": result.get("surface"),
        "production_spine": result.get("production_spine"),
        "catalog_link": result.get("catalog_link"),
        "canonical_capability_id": result.get("canonical_capability_id")
        or (gateway or {}).get("canonical_capability_id"),
    }


async def main() -> None:
    proofs = [await _prove(cid, user=user, label=label) for cid, user, label in CASES]
    by = {p["user_label"]: p for p in proofs}
    checks = {
        "no_skip_entitlement": all(not p["skip_entitlement_used"] for p in proofs),
        "count_10": len(proofs) == 10,
        "159_free_denied": by["canonical_103_free_denied"]["entitlement_allowed"] is False,
        "159_elite_allowed": by["pending_reused_elite_allowed"]["entitlement_allowed"] is True,
        "159_canonical_103": by["pending_reused_elite_allowed"]["canonical_id"] == 103,
        "159_batch04_spine": by["pending_reused_elite_allowed"]["production_spine"] == "batch04",
        "175_overlap_batch01": by["overlap_batch01_sentiment"]["production_spine"] == "batch01",
        "183_distinct_canonical": by["distinct_whale_free_allowed"]["canonical_id"] == 183,
        "161_free_denied": by["elite_gated_free_denied"]["entitlement_allowed"] is False,
        "161_elite_allowed": by["elite_institutional_delivery"]["entitlement_allowed"] is True,
    }
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "Batch04 entitlement gateway — 10 test cases (range 151-200)",
        "unique_capability_ids": sorted({p["capability_id"] for p in proofs}),
        "test_case_count": len(proofs),
        "script": "scripts/verify_entitlement_batch04_gateway_proof.py",
        "contract_test": "tests/cap646/test_batch04_gateway_canonical_entitlement_contract.py",
        "proofs": proofs,
        "checks": checks,
        "all_verified": all(checks.values()),
        "notes": {
            "159_183": "PENDING_CANONICAL_AUDIT — gateway uses canonical_id; REUSED-LINK not final",
            "175": "OVERLAP-PARTIAL — routes batch01 exclusively",
        },
    }
    path = ROOT / "docs/BATCH04_ENTITLEMENT_GATEWAY_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "checks": checks}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        raise SystemExit("Batch04 entitlement proof failed")


if __name__ == "__main__":
    asyncio.run(main())
