#!/usr/bin/env python3
"""HTTP live proof for official Batch 03 (IDs 101–150)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BATCH03_OVERLAP_BATCH01 = frozenset({103, 129})
REUSED_LINK_IDS = frozenset({106, 107, 110, 125})
ELITE_GATED_IDS = frozenset({103})
PRO_GATED_IDS = frozenset({110, 125})  # entitlement resolves via canonical #69 / #85


def _verified_anonymous_get(cid: int, response, body: dict, *, expected_spine: str, surface_ok: bool, reused_ok: bool) -> bool:
    if response.status_code != 200:
        return False
    if cid in ELITE_GATED_IDS or cid in PRO_GATED_IDS:
        ent = body.get("entitlement") or {}
        return (
            body.get("success") is False
            and ent.get("allowed") is False
            and ent.get("reason") in {"tier_insufficient", "teaser"}
        )
    return (
        bool(body.get("success"))
        and body.get("production_spine") in {expected_spine, "batch03_prep", "batch03"}
        and surface_ok
        and not body.get("oracle_fallback_error")
        and reused_ok
    )


def _catalog_link(body: dict) -> dict:
    link = body.get("catalog_link") or {}
    if link.get("duplicate_of"):
        return link
    for value in body.values():
        if isinstance(value, dict) and value.get("catalog_link"):
            return value["catalog_link"]
    return {}


def main() -> None:
    from fastapi.testclient import TestClient

    from cap646.batch01_dedicated import EXPECTED_SURFACE as BATCH01_SURFACES
    from cap646.batch03_dedicated import EXPECTED_SURFACE, GENERIC_SURFACES
    from cap646.batch03_production import BATCH03_IDS
    from dashboard import app

    client = TestClient(app)
    proofs = []
    for cid in sorted(BATCH03_IDS):
        response = client.get(f"/api/cap646/{cid}", params={"symbol": "BTC"})
        body = response.json()
        expected_spine = "batch01" if cid in BATCH03_OVERLAP_BATCH01 else "batch03"
        expected_surface = EXPECTED_SURFACE.get(cid) or BATCH01_SURFACES.get(cid)
        live_surface = body.get("surface")
        surface_ok = live_surface == expected_surface if expected_surface else live_surface not in GENERIC_SURFACES
        link = _catalog_link(body)
        reused_ok = True
        if cid in REUSED_LINK_IDS:
            reused_ok = link.get("classification") == "REUSED-LINK" and link.get("duplicate_of") in {63, 64, 69, 85}
        verified = _verified_anonymous_get(
            cid, response, body, expected_spine=expected_spine, surface_ok=surface_ok, reused_ok=reused_ok
        )
        proofs.append(
            {
                "capability_id": cid,
                "http_method": "GET",
                "http_path": f"/api/cap646/{cid}",
                "production_path": "dashboard.app -> api/routers/cap646.py::cap646_get -> cap978.unified.execute_unified -> cap646.runtime.execute_capability",
                "http_status": response.status_code,
                "success": body.get("success"),
                "surface": live_surface,
                "expected_surface": expected_surface,
                "production_spine": body.get("production_spine"),
                "expected_spine": expected_spine,
                "classification": body.get("classification"),
                "catalog_link": link or None,
                "overlap_batch01": cid in BATCH03_OVERLAP_BATCH01,
                "reused_link": cid in REUSED_LINK_IDS,
                "oracle_fallback_error": body.get("oracle_fallback_error"),
                "entitlement": body.get("entitlement"),
                "verified": verified,
            }
        )

    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "official batch03 IDs 101–150",
        "capability_ids": sorted(BATCH03_IDS),
        "overlap_batch01_ids": sorted(BATCH03_OVERLAP_BATCH01),
        "reused_link_ids": sorted(REUSED_LINK_IDS),
        "all_verified": all(p["verified"] for p in proofs),
        "proofs": proofs,
    }
    path = ROOT / "docs/BATCH03_PRODUCTION_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "count": len(proofs)}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        failed = [p["capability_id"] for p in proofs if not p["verified"]]
        raise SystemExit(f"HTTP proof failed for: {failed}")


if __name__ == "__main__":
    main()
