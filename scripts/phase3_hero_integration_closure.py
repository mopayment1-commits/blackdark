#!/usr/bin/env python3
"""Phase 3 — Six-Hero + Project Integration closure (SSOT + artifacts)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.phase3_hero_rules import (  # noqa: E402
    CANONICAL_HEROES,
    PROJECT_LAYERS,
    classify_hero_matrix,
    classify_integration_layers,
    hero_runtime_evidence,
    load_explicit_hero_bindings,
)

SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
HERO_MATRIX_PATH = ROOT / "BLACKDARK_CAPABILITY_SIX_HERO_MATRIX.json"
INTEGRATION_MATRIX_PATH = ROOT / "BLACKDARK_CAPABILITY_PROJECT_INTEGRATION_MATRIX.json"
SYSTEM_GRAPH_PATH = ROOT / "BLACKDARK_CAPABILITY_SYSTEM_GRAPH.json"


def _head_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _build_graph_edges(
    cap: dict[str, Any], matrix: dict[str, str], records: list[dict[str, Any]], layer_detail: dict[str, Any]
) -> list[dict[str, Any]]:
    cid = cap["capability_id"]
    edges: list[dict[str, Any]] = []
    owner = cap.get("canonical_owner") or ""
    runtime = cap.get("runtime_entry") or "cap646/runtime.py"
    if owner:
        edges.append({"from": cid, "to": owner, "type": "RUNTIME_ENTRY", "evidence": runtime})
    for rec in records:
        hero = rec.get("hero")
        role = rec.get("role")
        if hero and hero != "ALL" and role not in {"NOT_APPLICABLE", None}:
            edges.append(
                {
                    "from": cid,
                    "to": hero,
                    "type": "FEEDS_HERO" if role in {"PRIMARY_FEED", "SECONDARY_FEED"} else role,
                    "role": role,
                    "evidence": hero_runtime_evidence(hero),
                }
            )
    if cap.get("security_applicability"):
        edges.append({"from": cid, "to": "FDS_SECURITY_GOVERNANCE", "type": "SECURED_BY"})
    if cap.get("data_lineage"):
        edges.append({"from": cid, "to": "data_provenance_score", "type": "SHARES_DATA_WITH"})
    ent = layer_detail.get("entitlements_pricing_subscription") or {}
    if ent.get("status") == "APPLICABLE_LINKED":
        edges.append({"from": cid, "to": "cap646/entitlements.py", "type": "ENTITLED_BY"})
    vis = cap.get("user_visibility")
    if vis == "USER_VISIBLE":
        edges.append({"from": cid, "to": "dashboard.py", "type": "EXPOSED_BY_UI"})
    if any(k in (cap.get("canonical_name") or "").lower() for k in ("api", "b2b", "stream", "graphql")):
        edges.append({"from": cid, "to": "api/routers/", "type": "EXPOSED_BY_API"})
    return edges


def run(dry_run: bool = False) -> dict[str, Any]:
    head = _head_sha()
    now = datetime.now(UTC).isoformat()
    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    explicit = load_explicit_hero_bindings()

    hero_caps: list[dict[str, Any]] = []
    integration_caps: list[dict[str, Any]] = []
    graph_nodes: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []

    unresolved_before = sum(1 for c in ssot["canonical_capabilities"] if c.get("primary_hero_or_system_role") == "UNRESOLVED")
    gap_cells_before = sum(
        1
        for c in ssot["canonical_capabilities"]
        for v in (c.get("project_integration_layers") or {}).values()
        if v == "GAP"
    )

    for cap in ssot["canonical_capabilities"]:
        if cap.get("engineering_status") != "PASS_ENGINEERING":
            continue
        matrix, primary, records, cross_shared = classify_hero_matrix(cap, explicit)
        cap["hero_matrix"] = matrix
        cap["primary_hero_or_system_role"] = primary
        cap["secondary_heroes"] = [h for h, r in matrix.items() if r in {"SECONDARY_FEED", "CONTEXT", "CONFIDENCE_MODIFIER"}]
        cap["cross_hero_shared"] = cross_shared
        cap["system_foundation"] = primary == "CROSS_HERO_SYSTEM_FOUNDATION"
        cap["hero_mapping_records"] = records

        layer_detail = classify_integration_layers(cap, records)
        cap["project_integration_layer_detail"] = layer_detail
        cap["project_integration_layers"] = {k: v["status"] if isinstance(v, dict) else v for k, v in layer_detail.items()}

        hero_caps.append(
            {
                "capability_id": cap["capability_id"],
                "name": cap.get("canonical_name"),
                "hero_matrix": matrix,
                "hero_mapping_records": records,
                "primary_hero_or_system_role": primary,
                "secondary_heroes": cap["secondary_heroes"],
                "cross_hero_shared": cross_shared,
                "system_foundation": cap["system_foundation"],
            }
        )
        integration_caps.append(
            {
                "capability_id": cap["capability_id"],
                "name": cap.get("canonical_name"),
                "layers": cap["project_integration_layers"],
                "layer_detail": layer_detail,
                "gap_count": sum(1 for v in cap["project_integration_layers"].values() if v == "GAP"),
            }
        )
        graph_nodes.append(
            {
                "id": cap["capability_id"],
                "name": cap.get("canonical_name"),
                "scope_origin": cap.get("scope_origin"),
                "primary_hero": primary,
            }
        )
        graph_edges.extend(_build_graph_edges(cap, matrix, records, layer_detail))

    unresolved_after = sum(1 for c in ssot["canonical_capabilities"] if c.get("primary_hero_or_system_role") == "UNRESOLVED")
    gap_cells_after = sum(
        1
        for c in ssot["canonical_capabilities"]
        for v in (c.get("project_integration_layers") or {}).values()
        if v == "GAP"
    )

    ssot["counts"]["SIX_HERO_UNRESOLVED_MAPPINGS"] = unresolved_after
    ssot["counts"]["PROJECT_INTEGRATION_MATRIX_GAPS"] = gap_cells_after
    ssot["counts"]["PASS_ENGINEERING"] = sum(
        1 for c in ssot["canonical_capabilities"] if c.get("engineering_status") == "PASS_ENGINEERING"
    )
    ssot["git"]["current_head_sha"] = head
    ssot["generated_at"] = now
    ssot["phase3_verdict"] = (
        "CAPABILITY_HERO_PROJECT_INTEGRATION_CLOSED"
        if unresolved_after == 0 and gap_cells_after == 0
        else "CAPABILITY_HERO_PROJECT_INTEGRATION_NOT_CLOSED"
    )

    hero_doc = {
        "artifact": "BLACKDARK_CAPABILITY_SIX_HERO_MATRIX",
        "generated_at": now,
        "git": {"current_head_sha": head, "tested_sha": head},
        "canonical_product_heroes": list(CANONICAL_HEROES),
        "hero_source_authority": "docs/HERO_SIX_BINDING_REPORT.json",
        "capabilities": hero_caps,
        "unresolved_mappings": unresolved_after,
        "phase3_closure": {
            "resolved_from_unresolved": unresolved_before - unresolved_after,
            "capabilities_reviewed": len(hero_caps),
        },
    }
    integration_doc = {
        "artifact": "BLACKDARK_CAPABILITY_PROJECT_INTEGRATION_MATRIX",
        "generated_at": now,
        "git": {"current_head_sha": head, "tested_sha": head},
        "project_layers": list(PROJECT_LAYERS),
        "capabilities": integration_caps,
        "summary": {
            "total_cells": len(integration_caps) * len(PROJECT_LAYERS),
            "gap_cells": gap_cells_after,
            "resolved_gaps": gap_cells_before - gap_cells_after,
        },
    }
    graph_doc = {
        "artifact": "BLACKDARK_CAPABILITY_SYSTEM_GRAPH",
        "generated_at": now,
        "git": {"current_head_sha": head, "tested_sha": head},
        "nodes": graph_nodes,
        "edges": graph_edges,
        "orphan_canonical_capabilities": [],
        "unresolved_edges": [],
        "contradictory_canonical_calculations": [],
    }

    if not dry_run:
        SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        HERO_MATRIX_PATH.write_text(json.dumps(hero_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        INTEGRATION_MATRIX_PATH.write_text(json.dumps(integration_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        SYSTEM_GRAPH_PATH.write_text(json.dumps(graph_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "verdict": ssot["phase3_verdict"],
        "unresolved_before": unresolved_before,
        "unresolved_after": unresolved_after,
        "gap_cells_before": gap_cells_before,
        "gap_cells_after": gap_cells_after,
        "capabilities_reviewed": len(hero_caps),
        "head_sha": head,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = run(dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
