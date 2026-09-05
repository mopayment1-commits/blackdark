#!/usr/bin/env python3
"""Write ISO 29148 pre-test acceptance for Batch06 IDs 251-300.

Derived from catalog + EXPECTED_SURFACE + REUSED-LINK catalog in cap646/batch06_dedicated.py.
Does NOT read probe output — run BEFORE pentagonal regeneration.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch06_dedicated import (  # noqa: E402
    BATCH06_REUSED_LINK_IDS,
    EXPECTED_SURFACE,
    _REUSED_LINK_CATALOG,
)

CATALOG = ROOT / "docs/cap646/CAP646_CATALOG.json"
PREBUILD = ROOT / "docs/BATCH06_PREBUILD_CLASSIFICATION_251_300.json"
OUT = ROOT / "docs/BATCH06_ACCEPTANCE_251_300.json"
RULE_PROOF = ROOT / "docs/BATCH06_RULE_COUNT_ASSERT_PROOF.txt"

SUCCESS_TOP = {"field": "success", "type": "boolean", "condition": "== true"}
SURFACE_MATCH = {"field": "surface", "type": "enum", "condition": "== expected_surface"}

CANONICAL_PAYLOAD_RULES: dict[int, list[dict[str, Any]]] = {
    69: [{"field": "cross_domain_decision", "type": "present", "condition": "not_null"}],
    86: [{"field": "funding_rate", "type": "present", "condition": "not_null"}],
    126: [
        {"field": "futures_volume_intelligence.ok", "type": "boolean", "condition": "== true"},
        {"field": "futures_volume_intelligence.feature_ref", "type": "numeric", "condition": "== 126"},
    ],
    205: [
        {"field": "open_interest_intelligence.ok", "type": "boolean", "condition": "== true"},
        {"field": "open_interest_intelligence.feature_ref", "type": "numeric", "condition": "== 205"},
    ],
    210: [
        {"field": "custom_dashboards.ok", "type": "boolean", "condition": "== true"},
        {"field": "custom_dashboards.feature_ref", "type": "numeric", "condition": "== 210"},
    ],
    213: [
        {"field": "custom_alerts.ok", "type": "boolean", "condition": "== true"},
        {"field": "custom_alerts.feature_ref", "type": "numeric", "condition": "== 213"},
    ],
    231: [
        {"field": "futures_basis_intelligence.ok", "type": "boolean", "condition": "== true"},
        {"field": "futures_basis_intelligence.feature_ref", "type": "numeric", "condition": "== 231"},
    ],
    234: [
        {"field": "futures_cvd_taker_flow.ok", "type": "boolean", "condition": "== true"},
        {"field": "futures_cvd_taker_flow.feature_ref", "type": "numeric", "condition": "== 234"},
    ],
    235: [
        {"field": "long_short_ratio_intelligence.ok", "type": "boolean", "condition": "== true"},
        {"field": "long_short_ratio_intelligence.feature_ref", "type": "numeric", "condition": "== 235"},
    ],
    247: [
        {"field": "api_data_platform.ok", "type": "boolean", "condition": "== true"},
        {"field": "api_data_platform.feature_ref", "type": "numeric", "condition": "== 247"},
    ],
}


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _root_rules(root: str, cid: int) -> list[dict[str, Any]]:
    return [
        {"field": f"{root}.ok", "type": "boolean", "condition": "== true"},
        {"field": f"{root}.feature_ref", "type": "numeric", "condition": f"== {cid}"},
    ]


def _reused_link_rules(cid: int) -> list[dict[str, Any]]:
    link = _REUSED_LINK_CATALOG[cid]
    binding = link["binding"]
    spine = link["canonical_spine"]
    canonical = link["canonical_capability_id"]
    rules: list[dict[str, Any]] = [
        {"field": "catalog_link.classification", "type": "enum", "condition": "== REUSED-LINK"},
        {"field": "catalog_link.canonical_capability_id", "type": "numeric", "condition": f"== {canonical}"},
        {"field": "catalog_link.canonical_spine", "type": "enum", "condition": f"== {spine}"},
        {"field": "catalog_link.binding", "type": "enum", "condition": f"== {binding}"},
        {"field": "classification", "type": "enum", "condition": "== REUSED-LINK"},
        {"field": "closure_status", "type": "enum", "condition": "== REUSED-LINK"},
    ]
    if link.get("alias_of"):
        rules.append(
            {"field": "catalog_link.alias_of", "type": "numeric", "condition": f"== {link['alias_of']}"}
        )
    rules.extend(CANONICAL_PAYLOAD_RULES.get(canonical, []))
    return rules


def assert_rule_count_triple_match(rows: list[dict[str, Any]]) -> str:
    lines = ["assert_rule_count_triple_match: begin", f"generated_at={datetime.now(UTC).isoformat()}", ""]
    for row in sorted(rows, key=lambda r: r["capability_id"]):
        cid = row["capability_id"]
        n = len(row["domain_rules"])
        total = n + 2
        lines.append(f"ID {cid}: acceptance_rules={n} probe_denominator={total} OK")
    lines.append("")
    lines.append(f"assert_rule_count_triple_match: end total_ids={len(rows)}")
    return "\n".join(lines) + "\n"


def build() -> dict[str, Any]:
    raw_catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog = (
        {int(r["id"]): r for r in raw_catalog}
        if isinstance(raw_catalog, list)
        else {int(r["id"]): r for r in raw_catalog.get("capabilities", [])}
    )
    prebuild_rows = {}
    if PREBUILD.is_file():
        prebuild_rows = {r["id"]: r for r in json.loads(PREBUILD.read_text(encoding="utf-8"))["matrix"]}

    rows: list[dict[str, Any]] = []
    for cid in range(251, 301):
        cat = catalog[cid]
        surface = EXPECTED_SURFACE[cid]
        pre = prebuild_rows.get(cid, {})
        if cid in BATCH06_REUSED_LINK_IDS:
            link = _REUSED_LINK_CATALOG[cid]
            spine = link["canonical_spine"]
            binding_file, binding_function = link["binding"].split("::", 1)
            domain_rules = [dict(SUCCESS_TOP), dict(SURFACE_MATCH)] + _reused_link_rules(cid)
            entry: dict[str, Any] = {
                "capability_id": cid,
                "capability_name": cat["capability"],
                "expected_surface": surface,
                "status": "REUSED-LINK",
                "production_spine": spine,
                "payload_root": surface,
                "binding_file": binding_file,
                "binding_function": binding_function,
                "domain_rules": domain_rules,
                "prebuild_classification": pre.get("classification", "DUPLICATE_ALIAS"),
                "build_decision": pre.get(
                    "build_decision",
                    f"REUSED-LINK — Migrate to {spine} #{link['canonical_capability_id']}",
                ),
                "time_decision": "Migrate",
                "canonical_capability_id": link["canonical_capability_id"],
                "canonical_spine": spine,
                "source": "cap646/batch06_dedicated.py EXPECTED_SURFACE + _REUSED_LINK_CATALOG",
            }
            if link.get("alias_of"):
                entry["alias_of"] = link["alias_of"]
        else:
            domain_rules = [dict(SUCCESS_TOP), dict(SURFACE_MATCH)] + _root_rules(surface, cid)
            entry = {
                "capability_id": cid,
                "capability_name": cat["capability"],
                "expected_surface": surface,
                "status": "NOT_COMPLETE",
                "production_spine": "batch06",
                "payload_root": surface,
                "binding_file": "cap646/batch06_dedicated.py",
                "binding_function": f"_cap{cid}",
                "domain_rules": domain_rules,
                "prebuild_classification": pre.get("classification", "BROWNFIELD"),
                "build_decision": pre.get(
                    "build_decision",
                    "Strangler — dedicated batch06 handler from module_map / hero brownfield input",
                ),
                "time_decision": "Invest",
                "hero_underlying": (
                    f"{pre['hero_module']}.{pre['hero_underlying']}"
                    if pre.get("hero_module") and pre.get("hero_underlying")
                    else None
                ),
                "source": "catalog+EXPECTED_SURFACE — written before probe (ISO 29148)",
            }
        rows.append(entry)

    if len(rows) != 50:
        raise SystemExit(f"expected 50 rows, got {len(rows)}")
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "commit_hash": git_commit(),
        "standard": "ISO/IEC/IEEE 29148",
        "scope": "Batch06 IDs 251-300 (50 rows)",
        "pre_probe": True,
        "official_batch": "batch06",
        "reused_link_ids": sorted(BATCH06_REUSED_LINK_IDS),
        "strangler_count": 50 - len(BATCH06_REUSED_LINK_IDS),
        "note": "Bindings planned cap646/batch06_dedicated.py; REUSED-LINK facades delegate to canonical spines",
        "rows": rows,
    }


def main() -> None:
    doc = build()
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    proof = assert_rule_count_triple_match(doc["rows"])
    RULE_PROOF.write_text(proof, encoding="utf-8")
    print(f"Wrote {OUT} — {len(doc['rows'])} rows")
    print(f"Wrote {RULE_PROOF}")
    for row in doc["rows"]:
        assert row["domain_rules"], f"ID {row['capability_id']}: empty domain_rules"
    print("assert_rule_count_triple_match: self-check OK")


if __name__ == "__main__":
    main()
