#!/usr/bin/env python3
"""MECE duplicate/overlap audit for official batch IDs 1–100."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_inventory() -> dict:
    return json.loads((ROOT / "docs/CAPABILITIES_826_INVENTORY.json").read_text(encoding="utf-8"))


def _mece_pair(a: int, b: int, *, rationale: str) -> dict:
    inv = _load_inventory()["per_id"]
    pa, pb = inv[str(a)], inv[str(b)]
    return {
        "id_a": a,
        "id_b": b,
        "goal_a": pa["capability"],
        "goal_b": pb["capability"],
        "surface_a": pa.get("expected_surface"),
        "surface_b": pb.get("expected_surface"),
        "backend_a": pa.get("backend"),
        "backend_b": pb.get("backend"),
        "verdict": rationale.split(":")[0] if ":" in rationale else rationale,
        "rationale": rationale,
    }


def main() -> None:
    pairs = [
        _mece_pair(
            57,
            85,
            rationale="DISTINCT: #57=Profitability Map (profitability_analyzer_582, surface profitability_map) vs #85=Futures Open Interest Intelligence (derivatives_overview OI fields). User R2 cited 'Open Interest' for #57 — catalog registers Profitability Map; no MECE duplicate.",
        ),
        _mece_pair(55, 56, rationale="DISTINCT: NVT Fair-Value vs Token Screener — different catalog goals, batch01 overlap spine"),
        _mece_pair(85, 125, rationale="OVERLAP (LINK-ELIGIBLE): #125 duplicate_of #85 per REUSED_LINK_TAXONOMY; #125 in scope 101-150, not counted"),
        _mece_pair(63, 106, rationale="OVERLAP (LINK-ELIGIBLE): #106 duplicate_of #63; batch03 scope"),
        _mece_pair(53, 51, rationale="DISTINCT: #53 BTC-to-Macro Coupling vs #51 Macro & Traditional Finance Integration"),
    ]

    inv = _load_inventory()["per_id"]
    surface_dupes = {}
    for cid in range(1, 101):
        row = inv[str(cid)]
        surf = row.get("expected_surface")
        if surf:
            surface_dupes.setdefault(surf, []).append(int(cid))

    suspicious = {k: v for k, v in surface_dupes.items() if len(v) > 1}

    out = {
        "audited_at": datetime.now(UTC).isoformat(),
        "methodology": "TOGAF G189 MECE — compare catalog goal, surface, backend module",
        "requested_pairs": pairs,
        "duplicate_surfaces_in_1_100": suspicious,
        "note": "Only #57 vs #85 was flagged in CLOSURE-REJECT-02; #57 is NOT Open Interest per catalog",
    }
    path = ROOT / "docs/MECE_DUPLICATE_AUDIT_1_100.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(pairs), "duplicate_surfaces": suspicious}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
