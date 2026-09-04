#!/usr/bin/env python3
"""Entitlement gateway proof — batch05, all 43 strangler IDs (mirror batch03/batch04 pattern).

One pro-tier gateway_execute proof per strangler ID + REUSED-LINK spot checks.
Does NOT elevate production_aligned or batch05_independent.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch05_strangler_spine import STRANGLER_IMPLEMENTED_IDS  # noqa: E402

# Mirror batch03/batch04: representative REUSED-LINK + tier-denial spot checks beyond strangler sweep
EXTRA_CASES = [
    (214, {"tier": "pro"}, "reused_link_watchlists_batch01"),
    (232, {"tier": "pro"}, "reused_link_oi_canonical_205"),
    (245, {"tier": "pro"}, "reused_link_freshness_batch01"),
    (226, {"tier": "pro"}, "reused_link_cross_domain_69"),
    (226, {"tier": "free"}, "pro_gated_canonical_69_free_denied"),
]


async def _prove(capability_id: int, *, user: dict | None, label: str) -> dict:
    from cap646.catalog import canonical_id
    from cap646.entitlements import entitlement_engine
    from cap646.institutional_gateway import gateway_execute

    canonical = canonical_id(capability_id)
    runtime_ent = await entitlement_engine.check(canonical, user=user)
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
        "canonical_id": canonical,
        "user_label": label,
        "user": user,
        "path": "cap646.institutional_gateway.gateway_execute",
        "skip_entitlement_used": "skip_entitlement" in str(result),
        "entitlement_allowed": ent.get("allowed"),
        "entitlement_reason": ent.get("reason") or result.get("error"),
        "required_tier": ent.get("required_tier"),
        "runtime_entitlement_allowed": runtime_ent.get("allowed"),
        "runtime_entitlement_reason": runtime_ent.get("reason"),
        "entitlement_parity": ent.get("allowed") == runtime_ent.get("allowed"),
        "success": result.get("success"),
        "surface": result.get("surface"),
        "production_spine": result.get("production_spine"),
        "catalog_link": result.get("catalog_link"),
    }


async def main() -> None:
    strangler_ids = sorted(STRANGLER_IMPLEMENTED_IDS)
    proofs: list[dict] = []
    for cid in strangler_ids:
        proofs.append(await _prove(cid, user={"tier": "pro"}, label=f"strangler_{cid}_pro"))

    extra_labels: set[str] = set()
    for cid, user, label in EXTRA_CASES:
        if label in extra_labels:
            continue
        extra_labels.add(label)
        proofs.append(await _prove(cid, user=user, label=label))

    strangler_proofs = [p for p in proofs if p["user_label"].startswith("strangler_")]
    by = {p["user_label"]: p for p in proofs}

    checks = {
        "no_skip_entitlement": all(not p["skip_entitlement_used"] for p in proofs),
        "strangler_count_43": len(strangler_proofs) == 43,
        "strangler_ids_match": sorted(p["capability_id"] for p in strangler_proofs) == strangler_ids,
        "all_strangler_entitlement_parity": all(p["entitlement_parity"] for p in strangler_proofs),
        "all_strangler_pro_allowed": all(p["entitlement_allowed"] is True for p in strangler_proofs),
        "226_free_denied": by["pro_gated_canonical_69_free_denied"]["entitlement_allowed"] is False,
        "232_canonical_205": by["reused_link_oi_canonical_205"]["canonical_id"] == 205,
        "214_batch01_spine_or_facade": by["reused_link_watchlists_batch01"]["success"] is True,
        "245_freshness_success": by["reused_link_freshness_batch01"]["success"] is True,
    }

    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "scope": "Batch05 entitlement gateway — 43 strangler IDs + 5 REUSED-LINK spot checks",
        "strangler_capability_ids": strangler_ids,
        "strangler_test_case_count": len(strangler_proofs),
        "total_test_case_count": len(proofs),
        "script": "scripts/verify_entitlement_batch05_gateway_proof.py",
        "contract_test": "tests/cap646/test_batch05_gateway_canonical_entitlement_contract.py",
        "proofs": proofs,
        "checks": checks,
        "all_verified": all(checks.values()),
        "batch05_independent": 0,
        "production_aligned_count": 0,
        "notes": {
            "mirror": "Same gateway_execute + entitlement_engine.check(canonical_id) parity as batch03/batch04",
            "elevation": "Proof only — does NOT mark any ID PRODUCTION-ALIGNED",
        },
    }
    path = ROOT / "docs/BATCH05_ENTITLEMENT_GATEWAY_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "checks": checks}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        raise SystemExit("Batch05 entitlement proof failed")


if __name__ == "__main__":
    asyncio.run(main())
