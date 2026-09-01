#!/usr/bin/env python3
"""HTTP live proof for the 11 formerly-NOT_COMPLETE batch01 capabilities."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXED_IDS = [8, 9, 15, 16, 17, 24, 26, 31, 32, 35, 42]


def main() -> None:
    from fastapi.testclient import TestClient
    from dashboard import app

    client = TestClient(app)
    proofs = []
    for cid in FIXED_IDS:
        response = client.get(f"/api/cap646/{cid}", params={"symbol": "BTC"})
        body = response.json()
        proofs.append(
            {
                "capability_id": cid,
                "http_method": "GET",
                "http_path": f"/api/cap646/{cid}",
                "production_path": "dashboard.app -> api/routers/cap646.py::cap646_get -> cap978.unified.execute_unified -> cap646.runtime.execute_capability",
                "http_status": response.status_code,
                "success": body.get("success"),
                "surface": body.get("surface"),
                "production_spine": body.get("production_spine"),
                "classification": body.get("classification"),
                "oracle_fallback_error": body.get("oracle_fallback_error"),
                "verified": (
                    response.status_code == 200
                    and bool(body.get("success"))
                    and body.get("production_spine") == "batch01"
                    and not body.get("oracle_fallback_error")
                ),
            }
        )

    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "11 formerly-NOT_COMPLETE official batch01 IDs",
        "capability_ids": FIXED_IDS,
        "all_verified": all(p["verified"] for p in proofs),
        "proofs": proofs,
    }
    path = ROOT / "docs/BATCH01_HTTP_PROOF_11_FIXED.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "count": len(proofs)}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        failed = [p["capability_id"] for p in proofs if not p["verified"]]
        raise SystemExit(f"HTTP proof failed for: {failed}")


if __name__ == "__main__":
    main()
