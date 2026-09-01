#!/usr/bin/env python3
"""HTTP live proof for official Batch 02 (IDs 51–100)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OVERLAP_BATCH01 = frozenset({55, 56, 59, 60})


def main() -> None:
    from fastapi.testclient import TestClient
    from cap646.batch02_dedicated import EXPECTED_SURFACE, GENERIC_SURFACES
    from cap646.batch01_dedicated import EXPECTED_SURFACE as BATCH01_SURFACES
    from cap646.batch02_production import OFFICIAL_BATCH02_IDS
    from dashboard import app

    client = TestClient(app)
    proofs = []
    for cid in sorted(OFFICIAL_BATCH02_IDS):
        response = client.get(f"/api/cap646/{cid}", params={"symbol": "BTC"})
        body = response.json()
        expected_spine = "batch01" if cid in OVERLAP_BATCH01 else "batch02"
        expected_surface = EXPECTED_SURFACE.get(cid) or BATCH01_SURFACES.get(cid)
        live_surface = body.get("surface")
        surface_ok = live_surface == expected_surface if expected_surface else live_surface not in GENERIC_SURFACES
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
                "overlap_batch01": cid in OVERLAP_BATCH01,
                "oracle_fallback_error": body.get("oracle_fallback_error"),
                "verified": (
                    response.status_code == 200
                    and bool(body.get("success"))
                    and body.get("production_spine") == expected_spine
                    and surface_ok
                    and not body.get("oracle_fallback_error")
                ),
            }
        )

    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "official batch02 IDs 51–100",
        "capability_ids": sorted(OFFICIAL_BATCH02_IDS),
        "overlap_batch01_ids": sorted(OVERLAP_BATCH01),
        "all_verified": all(p["verified"] for p in proofs),
        "proofs": proofs,
    }
    path = ROOT / "docs/BATCH02_HTTP_PROOF_51_100.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "count": len(proofs)}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        failed = [p["capability_id"] for p in proofs if not p["verified"]]
        raise SystemExit(f"HTTP proof failed for: {failed}")


if __name__ == "__main__":
    main()
