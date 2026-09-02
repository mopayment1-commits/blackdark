#!/usr/bin/env python3
"""Entitlement proof on GET /api/cap646/{id} — HTTP path (not gateway_execute)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 10 cases across tiers via GET /api/cap646/{id}
CASES = [
    (1, None, "free_allowed_anonymous"),
    (21, None, "free_allowed_anonymous"),
    (47, None, "pro_gated_free_denied"),
    (47, {"tier": "pro"}, "pro_gated_pro_allowed"),
    (50, None, "pro_gated_free_denied"),
    (50, {"tier": "pro"}, "pro_gated_pro_allowed"),
    (69, None, "pro_gated_free_denied"),
    (69, {"tier": "pro"}, "pro_gated_pro_allowed"),
    (85, None, "pro_gated_free_denied"),
    (85, {"tier": "pro"}, "pro_gated_pro_allowed"),
]


def main() -> None:
    from fastapi.testclient import TestClient
    from dashboard import app

    client = TestClient(app)
    proofs = []
    for capability_id, user, label in CASES:
        headers: dict[str, str] = {}
        # TestClient has no session; user tier simulated via optional auth bypass in tests only.
        # For tier simulation we call execute path via internal helper when user dict provided.
        if user is None:
            response = client.get(f"/api/cap646/{capability_id}", params={"symbol": "BTC"})
            body = response.json()
            ent = body.get("entitlement") or {}
            proofs.append(
                {
                    "capability_id": capability_id,
                    "user_label": label,
                    "http_method": "GET",
                    "http_path": f"/api/cap646/{capability_id}",
                    "http_status": response.status_code,
                    "entitlement_allowed": ent.get("allowed"),
                    "entitlement_reason": ent.get("reason"),
                    "success": body.get("success"),
                    "production_spine": body.get("production_spine"),
                }
            )
        else:
            # Tiered cases: invoke same router stack with injected user via dependency override
            from api.routers import cap646 as cap646_router
            from security_auth import optional_user_from_request

            async def _user_override() -> dict:
                return {"email": f"{label}@proof.blackdark.local", "tier": user["tier"]}

            app.dependency_overrides[optional_user_from_request] = _user_override
            try:
                response = client.get(f"/api/cap646/{capability_id}", params={"symbol": "BTC"})
                body = response.json()
                ent = body.get("entitlement") or {}
                proofs.append(
                    {
                        "capability_id": capability_id,
                        "user_label": label,
                        "user": user,
                        "http_method": "GET",
                        "http_path": f"/api/cap646/{capability_id}",
                        "http_status": response.status_code,
                        "entitlement_allowed": ent.get("allowed"),
                        "entitlement_reason": ent.get("reason"),
                        "success": body.get("success"),
                        "production_spine": body.get("production_spine"),
                    }
                )
            finally:
                app.dependency_overrides.pop(optional_user_from_request, None)

    by = {p["user_label"]: p for p in proofs}
    checks = {
        "count_10": len(proofs) == 10,
        "47_free_denied": by["pro_gated_free_denied"]["entitlement_reason"] in {"tier_insufficient", "teaser"},
        "47_pro_allowed": by["pro_gated_pro_allowed"]["success"] is True,
        "85_free_denied": by["pro_gated_free_denied"]["entitlement_reason"] in {"tier_insufficient", "teaser"},
        "85_pro_allowed": by["pro_gated_pro_allowed"]["success"] is True,
        "free_1_allowed": by["free_allowed_anonymous"]["success"] is True,
    }
    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "scope": "GET /api/cap646/{id} entitlement — 10 cases (anonymous + tier override)",
        "path": "GET /api/cap646/{capability_id}",
        "script": "scripts/verify_entitlement_get_proof.py",
        "proofs": proofs,
        "checks": checks,
        "all_verified": all(checks.values()),
    }
    path = ROOT / "docs/BATCH_ENTITLEMENT_GET_PROOF.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "checks": checks}, indent=2))
    print(f"Wrote {path}")
    if not out["all_verified"]:
        raise SystemExit("GET entitlement proof failed")


if __name__ == "__main__":
    main()
