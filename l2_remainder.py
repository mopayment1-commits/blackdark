"""Honest remainder of institutional L2 — never invent AMM CEX-style books."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def catalog_l2_remainder() -> dict[str, Any]:
    """DEX catalog slots stay synthetic_mid. Bybit remains geo-sensitive."""
    registry = Path("data/universe_registry.json")
    venues: list[dict[str, Any]] = []
    if registry.is_file():
        try:
            body = json.loads(registry.read_text(encoding="utf-8"))
            rows = body if isinstance(body, list) else (body.get("exchanges") or body.get("venues") or [])
        except json.JSONDecodeError:
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            provider = str(row.get("provider") or "")
            vid = str(row.get("id") or "")
            if provider == "dex" or vid == "bybit":
                venues.append(
                    {
                        "id": vid,
                        "name": row.get("name"),
                        "provider": provider or "ccxt",
                        "depth_class": "synthetic_mid",
                        "reason": "amm_pool_not_cex_l2" if provider == "dex" else "bybit_geo_sensitive",
                    }
                )
    four: dict[str, Any] = {}
    evidence = Path("docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json")
    if evidence.is_file():
        try:
            four = json.loads(evidence.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            four = {}
    b3 = four.get("blocker_3_full_mesh_100") or {}
    l2_pct = b3.get("institutional_l2_coverage_percent")
    return {
        "ok": True,
        "product_complete": False,
        "full_mesh_l2_complete": False,
        "institutional_l2_coverage_percent": l2_pct,
        "remainder_count": len(venues),
        "remainder": venues,
        "honesty": (
            "synthetic_mid ≠ venue_l2. AMM pools are not fabricated as CEX ladders. "
            "Bybit order hosts may be geo-blocked."
        ),
        "proved_at": _utcnow(),
    }
