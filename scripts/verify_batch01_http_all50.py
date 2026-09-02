#!/usr/bin/env python3
"""HTTP live proof for all official Batch 01 IDs (1–50)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PRO_GATED_IDS = frozenset({47, 48, 69, 85})


def _verified_anonymous_get(cid: int, response, body: dict, *, expected_spine: str, surface_ok: bool) -> bool:
    if response.status_code != 200:
        return False
    if cid in PRO_GATED_IDS:
        ent = body.get("entitlement") or {}
        return (
            body.get("success") is False
            and ent.get("allowed") is False
            and ent.get("reason") in {"tier_insufficient", "teaser"}
        )
    return (
        bool(body.get("success"))
        and body.get("production_spine") == expected_spine
        and surface_ok
        and not body.get("oracle_fallback_error")
    )


def main() -> None:
    from fastapi.testclient import TestClient
    from cap646.batch01_dedicated import EXPECTED_SURFACE, GENERIC_SURFACES
    from cap646.batch01_production import OFFICIAL_BATCH01_IDS
    from dashboard import app

    client = TestClient(app)
    proofs = []
    for cid in sorted(OFFICIAL_BATCH01_IDS):
        response = client.get(f"/api/cap646/{cid}", params={"symbol": "BTC"})
        body = response.json()
        expected_surface = EXPECTED_SURFACE.get(cid)
        live_surface = body.get("surface")
        surface_ok = live_surface == expected_surface if expected_surface else live_surface not in GENERIC_SURFACES
        proofs.append(
            {
                "capability_id": cid,
                "http_method": "GET",
                "http_path": f"/api/cap646/{cid}",
                "http_status": response.status_code,
                "success": body.get("success"),
                "surface": live_surface,
                "expected_surface": expected_surface,
                "production_spine": body.get("production_spine"),
                "classification": body.get("classification"),
                "oracle_fallback_error": body.get("oracle_fallback_error"),
                "entitlement": body.get("entitlement"),
                "verified": _verified_anonymous_get(
                    cid, response, body, expected_spine="batch01", surface_ok=surface_ok
                ),
            }
        )

    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "official batch01 IDs 1–50",
        "capability_ids": sorted(OFFICIAL_BATCH01_IDS),
        "all_verified": all(p["verified"] for p in proofs),
        "proofs": proofs,
    }
    path = ROOT / "docs/BATCH01_HTTP_PROOF_1_50.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "count": len(proofs)}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        failed = [p["capability_id"] for p in proofs if not p["verified"]]
        raise SystemExit(f"HTTP proof failed for: {failed}")


if __name__ == "__main__":
    main()
