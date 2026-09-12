"""Six Heroes binding resolver for CAPABILITY_BUILD_826 program.

Maps capability IDs to primary Hero, entry path, and binding status using the
canonical HERO_ENGINES registry (docs/HERO_SIX_BINDING_REPORT.json lineage).
"""
from __future__ import annotations

from typing import Any

# Canonical six-hero engines — capability_id membership from pentagonal binding report.
HERO_ENGINES: dict[str, dict[str, Any]] = {
    "Single-Sentence Oracle": {
        "live_endpoint": {"method": "GET", "path": "/api/oracle/persona-clarity/demo"},
        "ui_path": "/dashboard",
        "capability_ids": {
            24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 40, 47, 48, 50, 55, 56, 59, 66, 69, 86, 89, 90,
        },
    },
    "Public Accuracy Ledger": {
        "live_endpoint": {"method": "GET", "path": "/api/oracle/audit-chain/verify"},
        "ui_path": "/oracle-accuracy",
        "capability_ids": {61, 63, 64, 65, 100},
    },
    "Arbitrage Scanner": {
        "live_endpoint": {"method": "GET", "path": "/api/arbitrage/scanner/status"},
        "ui_path": "/dashboard",
        "capability_ids": {11, 40, 47, 48, 50, 52, 57, 69, 82, 83, 85, 86, 87, 88, 89},
    },
    "Whale Signal vs Noise": {
        "live_endpoint": {"method": "GET", "path": "/api/whale/signal-vs-noise"},
        "ui_path": "/dashboard",
        "capability_ids": {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 72, 75, 81, 85, 86, 88, 91, 92, 98},
    },
    "Stealth Advisor": {
        "live_endpoint": {"method": "POST", "path": "/api/whale/stealth-advisor"},
        "ui_path": "/dashboard",
        "capability_ids": {40, 50, 85, 86, 87, 88},
    },
    "B2B Feed": {
        "live_endpoint": {"method": "GET", "path": "/api/b2b/demo"},
        "ui_path": "/institutional",
        "capability_ids": {67, 68, 71, 74, 77, 81, 84, 91, 92, 98, 99, 100},
    },
}

# Batch01 build IDs with explicit hero when not in HERO_ENGINES lists above.
_BATCH01_FALLBACK: dict[int, str] = {
    17: "Whale Signal vs Noise",
}

# Batch02 (26–50) — oracle / on-chain / market surfaces
_BATCH02_FALLBACK: dict[int, str] = {
    **{cid: "Single-Sentence Oracle" for cid in range(26, 36)},
    36: "Whale Signal vs Noise",
    37: "Whale Signal vs Noise",
    38: "Whale Signal vs Noise",
    39: "Whale Signal vs Noise",
    41: "Whale Signal vs Noise",
    42: "Whale Signal vs Noise",
    43: "Whale Signal vs Noise",
    44: "Whale Signal vs Noise",
    45: "Whale Signal vs Noise",
    46: "Whale Signal vs Noise",
    47: "Single-Sentence Oracle",
    48: "Single-Sentence Oracle",
    49: "Arbitrage Scanner",
    50: "Single-Sentence Oracle",
}


def _heroes_for(cid: int) -> list[str]:
    return [name for name, meta in HERO_ENGINES.items() if cid in meta["capability_ids"]]


def _primary_hero_for(cid: int) -> str | None:
    hits = _heroes_for(cid)
    if hits:
        return hits[0]
    if cid in _BATCH01_FALLBACK:
        return _BATCH01_FALLBACK[cid]
    return _BATCH02_FALLBACK.get(cid)


def hero_binding_for(cid: int) -> dict[str, Any]:
    """Return primary_hero, hero_entry_path, hero_binding_status for register."""
    heroes = _heroes_for(cid)
    if not heroes:
        fb = _BATCH01_FALLBACK.get(cid) or _BATCH02_FALLBACK.get(cid)
        if fb:
            heroes = [fb]
    hero = heroes[0] if heroes else None
    if not hero:
        return {
            "primary_hero": None,
            "secondary_heroes": [],
            "hero_entry_path": None,
            "hero_ui_path": None,
            "hero_binding_status": "UNBOUND",
        }
    meta = HERO_ENGINES[hero]
    cap_path = f"/api/cap646/{cid}/execute"
    entry = meta["live_endpoint"]["path"]
    return {
        "primary_hero": hero,
        "secondary_heroes": heroes[1:],
        "hero_entry_path": f"{entry} → {cap_path}",
        "hero_ui_path": meta.get("ui_path", "/cap646"),
        "hero_binding_status": "BOUND",
        "cap646_execute_path": cap_path,
    }


def enrich_binding_row(cid: int, row: dict[str, Any]) -> dict[str, Any]:
    binding = hero_binding_for(cid)
    row.update(binding)
    if binding["hero_binding_status"] == "UNBOUND" and row.get("status") == "COMPLETE_V6":
        blockers = list(row.get("blocker") or [])
        blockers.append("hero_binding:UNBOUND")
        row["status"] = "PARTIAL"
        row["blocker"] = blockers
    return row
