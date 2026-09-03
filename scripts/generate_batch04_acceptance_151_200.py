#!/usr/bin/env python3
"""Write ISO 29148 pre-test acceptance criteria for Batch04 IDs 151-200.

Derived from RTM + planned handler bindings (cap646/batch04_dedicated.py).
Does NOT read probe output — run BEFORE any pentagonal regeneration.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RTM = ROOT / "docs/BATCH04_RTM_151_200.json"
OUT = ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json"

SUCCESS_TOP = {"field": "success", "type": "boolean", "condition": "== true"}
SURFACE_MATCH = {"field": "surface", "type": "enum", "condition": "== expected_surface"}


def _slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")[:56]


def _default_rules(root: str, capability_id: int) -> list[dict[str, Any]]:
    return [
        {"field": f"{root}.ok", "type": "boolean", "condition": "== true"},
        {"field": f"{root}.feature_ref", "type": "numeric", "condition": f"== {capability_id}"},
    ]


# Per-ID overrides (ISO 29148 pre-probe — not from runtime probe)
_SPECS: dict[int, dict[str, Any]] = {
    159: {
        "status": "NOT_COMPLETE",
        "spine": "batch04",
        "payload_root": "api_data_platform",
        "domain_rules": [
            {"field": "catalog_link.duplicate_of", "type": "numeric", "condition": "== 103"},
            {"field": "catalog_link.classification", "type": "enum", "condition": "== REUSED-LINK"},
            {"field": "api_data_platform.institutional_api", "type": "enum", "condition": "== /api/institutional"},
        ],
        "notes": "PENDING_CANONICAL_AUDIT — canonical #103 not PRODUCTION-ALIGNED; REUSED-LINK not final",
    },
    175: {
        "status": "OVERLAP-PARTIAL",
        "spine": "batch01",
        "payload_root": "social_sentiment",
        "domain_rules": [
            {"field": "production_spine", "type": "enum", "condition": "== batch01"},
            {"field": "social_sentiment.feature_ref", "type": "numeric", "condition": "== 175"},
        ],
        "notes": "OVERLAP-PARTIAL — legacy batch01 extension; excluded from batch04_independent",
    },
    183: {
        "status": "NOT_COMPLETE",
        "payload_root": "whale_transaction",
        "domain_rules": [
            {"field": "catalog_link.duplicate_of", "type": "numeric", "condition": "== 130"},
            {"field": "catalog_link.classification", "type": "enum", "condition": "== REUSED-LINK"},
            {"field": "whale_transaction.risk_score", "type": "numeric", "condition": ">= 0"},
        ],
        "notes": "PENDING_CANONICAL_AUDIT — DISTINCT whale payload; canonical #130 not PRODUCTION-ALIGNED",
    },
}


def build_acceptance() -> dict[str, Any]:
    rtm = json.loads(RTM.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for rtm_row in sorted(rtm["rows"], key=lambda r: r["id"]):
        cid = rtm_row["id"]
        surface = rtm_row["expected_surface_planned"]
        spec = _SPECS.get(
            cid,
            {
                "payload_root": surface,
                "domain_rules": _default_rules(surface, cid),
            },
        )
        rules = [dict(SUCCESS_TOP), dict(SURFACE_MATCH)] + [dict(r) for r in spec["domain_rules"]]
        entry: dict[str, Any] = {
            "capability_id": cid,
            "capability_name": rtm_row["capability"],
            "expected_surface": surface,
            "status": spec.get("status", rtm_row["status"]),
            "production_spine": spec.get("spine", "batch04"),
            "payload_root": spec.get("payload_root"),
            "binding_file": rtm_row["binding_file_planned"],
            "binding_function": rtm_row["binding_function_planned"],
            "domain_rules": rules,
            "prebuild_classification": rtm_row["prebuild_classification"],
            "build_decision": rtm_row["build_decision"],
            "hero_underlying": rtm_row.get("hero_underlying"),
            "source": "catalog+planned_handler_contract — written before probe (ISO 29148)",
        }
        if spec.get("notes"):
            entry["notes"] = spec["notes"]
        if rtm_row.get("duplicate_candidates"):
            entry["duplicate_candidates"] = rtm_row["duplicate_candidates"]
        rows.append(entry)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "standard": "ISO/IEC/IEEE 29148",
        "scope": "Batch04 IDs 151-200 (50 rows)",
        "pre_probe": True,
        "official_batch": "batch04",
        "note": "Bindings in cap646/batch04_dedicated.py — catalog-aligned handlers (build phase)",
        "rows": rows,
    }


def main() -> None:
    doc = build_acceptance()
    assert len(doc["rows"]) == 50, f"expected 50 acceptance rows, got {len(doc['rows'])}"
    for row in doc["rows"]:
        assert row["domain_rules"], f"ID {row['capability_id']}: domain_rules must not be empty"
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(doc['rows'])} capabilities)")


if __name__ == "__main__":
    main()
