#!/usr/bin/env python3
"""Entitlement live proof — full gateway path (no skip_entitlement)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
        "path": "cap646.institutional_gateway.gateway_execute -> cap646.runtime.execute_capability (entitlement enforced)",
        "entitlement_allowed": ent.get("allowed", result.get("success") is not False and result.get("error") != "entitlement_denied"),
        "entitlement_reason": ent.get("reason") or result.get("error"),
        "success": result.get("success"),
        "surface": result.get("surface"),
        "production_spine": result.get("production_spine"),
        "classification": result.get("classification"),
    }


async def main() -> None:
    cases = [
        (1, {"tier": "free"}, "anonymous_free"),
        (8, {"tier": "free"}, "free_tier_user"),
        (24, {"tier": "pro"}, "pro_tier_no_ssot_override"),
        (47, {"tier": "free"}, "free_user_pro_gated"),
        (47, {"tier": "pro"}, "pro_tier_spot_metrics"),
    ]
    proofs = [await _prove(cid, user=user, label=label) for cid, user, label in cases]
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "Entitlement gateway path (no skip_entitlement)",
        "proofs": proofs,
        "expectations": {
            "1_free": "allowed + batch01 spine",
            "8_free": "allowed + batch01 spine",
            "24_pro": "allowed + batch01 spine",
            "47_free": "denied tier_insufficient",
            "47_pro": "allowed",
            "103_elite": "allowed (if subscription active) or tier path exercised",
        },
    }
    # Validate key expectations
    by_key = {f"{p['capability_id']}_{p['user_label']}": p for p in proofs}
    checks = {
        "1_allowed": by_key["1_anonymous_free"]["entitlement_allowed"] is True,
        "8_allowed": by_key["8_free_tier_user"]["entitlement_allowed"] is True,
        "24_pro_allowed": by_key["24_pro_tier_no_ssot_override"]["entitlement_allowed"] is True,
        "47_free_denied": by_key["47_free_user_pro_gated"]["entitlement_reason"] in {"tier_insufficient", "teaser"},
        "47_pro_allowed": by_key["47_pro_tier_spot_metrics"]["entitlement_allowed"] is True,
    }
    out["checks"] = checks
    out["all_verified"] = all(checks.values())

    path = ROOT / "docs/BATCH01_ENTITLEMENT_GATEWAY_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "checks": checks}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    asyncio.run(main())
