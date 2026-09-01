#!/usr/bin/env python3
"""Entitlement gateway proof for official Batch 02 (IDs 51–100) — no skip_entitlement."""

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
        (51, {"tier": "free"}, "free_macro_tradfi"),
        (53, {"tier": "free"}, "free_btc_macro_coupling"),
        (69, {"tier": "pro"}, "pro_cross_domain_decision"),
        (85, {"tier": "pro"}, "pro_futures_open_interest"),
        (100, {"tier": "free"}, "free_research_reports"),
        (103, {"tier": "free"}, "free_denied_elite_gated_reference"),
    ]
    proofs = [await _prove(cid, user=user, label=label) for cid, user, label in cases]
    by_key = {f"{p['capability_id']}_{p['user_label']}": p for p in proofs}
    checks = {
        "51_free_allowed": by_key["51_free_macro_tradfi"]["entitlement_allowed"] is True
        and by_key["51_free_macro_tradfi"]["production_spine"] == "batch02",
        "53_free_allowed": by_key["53_free_btc_macro_coupling"]["entitlement_allowed"] is True
        and by_key["53_free_btc_macro_coupling"]["production_spine"] == "batch02",
        "69_pro_allowed": by_key["69_pro_cross_domain_decision"]["entitlement_allowed"] is True
        and by_key["69_pro_cross_domain_decision"]["production_spine"] == "batch02",
        "85_pro_allowed": by_key["85_pro_futures_open_interest"]["entitlement_allowed"] is True
        and by_key["85_pro_futures_open_interest"]["production_spine"] == "batch02",
        "100_free_allowed": by_key["100_free_research_reports"]["entitlement_allowed"] is True
        and by_key["100_free_research_reports"]["production_spine"] == "batch02",
        "103_free_denied": by_key["103_free_denied_elite_gated_reference"]["entitlement_allowed"] is False,
    }
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "Official batch02 entitlement gateway (no skip_entitlement)",
        "official_batch": "batch02",
        "proofs": proofs,
        "checks": checks,
        "all_verified": all(checks.values()),
        "note": "Deny case #103 exercises elite gate from same gateway path used by batch02 traffic",
    }
    path = ROOT / "docs/BATCH02_ENTITLEMENT_GATEWAY_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "checks": checks}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        raise SystemExit("batch02 entitlement proof failed")


if __name__ == "__main__":
    asyncio.run(main())
