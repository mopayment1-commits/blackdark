#!/usr/bin/env python3
"""Initial MECE + jscpd duplication audit for official Batch04 IDs 151-200 (Phase 1)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BATCH04_INITIAL_DUPLICATION_SCAN.json"
BATCH04_RANGE = range(151, 201)

# Confirmed / candidate pairs from RTM + hero + catalog
CONFIRMED_PAIRS = [
    {"a": 159, "b": 103, "scope": "151-200 vs 1-150", "classification": "DUPLICATE-CONFIRMED→REUSED-LINK", "evidence": "REPEAT_CANONICAL API Data Platform; gap DUPLICATE/ALREADY_COVERED"},
    {"a": 175, "b": "batch01", "scope": "batch01 overlap", "classification": "OVERLAP-PARTIAL", "evidence": "LEGACY_BATCH01_EXTENSION_IDS; n14_excluded_legacy_extension"},
    {"a": 183, "b": 130, "scope": "hero layer", "classification": "REUSED-LINK candidate", "evidence": "hero exact_fn_reuse transaction_risk_insight_130"},
]

INTERNAL_CLUSTERS = [
    {"ids": list(range(167, 179)), "name": "social_sentiment_volume_cluster", "classification": "OVERLAP-PARTIAL candidate", "action": "MECE semantic audit required"},
    {"ids": list(range(187, 192)), "name": "exchange_flow_cluster", "classification": "OVERLAP-PARTIAL candidate", "action": "MECE semantic audit required"},
    {"ids": list(range(194, 201)), "name": "onchain_valuation_metrics_cluster", "classification": "OVERLAP-PARTIAL candidate", "action": "MECE semantic audit required"},
    {"ids": [151, 152, 157, 163], "name": "research_reporting_cluster", "classification": "OVERLAP-PARTIAL candidate", "action": "distinct vs batch03 research IDs 100/109"},
]

HERO_LAYER_FILES = [
    "bd_platform/data_sources_layer.py",
    "bd_platform/intelligence_analysis_layer.py",
    "bd_platform/risk_infrastructure_layer.py",
    "bd_platform/arbitrage_portfolio_ux_layer.py",
    "bd_platform/derivatives_ta_research_layer.py",
    "bd_platform/onchain_platform_layer.py",
]


def _jscpd_report() -> dict[str, Any]:
    out_dir = ROOT / "docs/.jscpd-batch04-phase1"
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = [p for p in HERO_LAYER_FILES if (ROOT / p).is_file()]
    proc = subprocess.run(
        [
            "npx",
            "--yes",
            "jscpd",
            "--min-lines",
            "8",
            "--min-tokens",
            "60",
            "--reporters",
            "json",
            "--output",
            str(out_dir),
            *existing,
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=180,
    )
    report_path = out_dir / "jscpd-report.json"
    if report_path.is_file():
        data = json.loads(report_path.read_text(encoding="utf-8"))
        stats = data.get("statistics", {}).get("total", {})
        return {
            "exit_code": proc.returncode,
            "files_scanned": existing,
            "duplicated_lines": stats.get("duplicatedLines"),
            "duplicated_tokens": stats.get("duplicatedTokens"),
            "total_lines": stats.get("sources"),
            "clones": len(data.get("duplicates", [])),
            "report_path": str(report_path.relative_to(ROOT)),
        }
    return {"exit_code": proc.returncode, "stderr": proc.stderr[-500:], "files_scanned": existing}


def _hero_option_a_search() -> dict[str, Any]:
    """Scope (4): Option-A / out-of-batch IDs in SSOT — search performed."""
    inv = json.loads((ROOT / "docs/CAPABILITIES_826_INVENTORY.json").read_text(encoding="utf-8"))
    option_a = inv["three_separate_counts"]["progress_826_equation"].get("k_option_a_prebatch", 4)
    option_ids = [338, 500, 507, 534]
    overlaps = []
    for oid in option_ids:
        row = inv["per_id"].get(str(oid), {})
        overlaps.append({"option_a_id": oid, "capability": row.get("capability"), "status": row.get("status")})
    return {
        "scope": "Option-A pre-batch IDs vs 151-200",
        "result": "NOT_APPLICABLE — no direct ID collision; semantic overlap audit deferred to cluster review",
        "option_a_ids_checked": overlaps,
        "option_a_count": option_a,
    }


def main() -> None:
    jscpd = _jscpd_report()
    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Batch04 Phase-1 initial duplication scan (IDs 151-200)",
        "standards": ["TOGAF/MECE capability overlap", "Roy & Cordy Type-1..4", "CWE-1041 / jscpd"],
        "scopes": {
            "D1_internal_151_200": {
                "pairs_confirmed": CONFIRMED_PAIRS,
                "clusters_candidate": INTERNAL_CLUSTERS,
                "distinct_default": "remaining IDs pending per-pair MECE after dedicated handlers exist",
            },
            "D1_vs_1_150": {
                "pairs": [p for p in CONFIRMED_PAIRS if p["scope"] != "hero layer"],
                "note": "Full 50×150 matrix not exhaustively run — confirmed pairs listed; expand during implementation",
            },
            "D1_hero_batch_scopes": {
                "files_searched": HERO_LAYER_FILES,
                "split_brain_warning": "Hero layer ID numbers reuse different semantics than official catalog for several IDs (e.g. catalog #153 ≠ hero #153 fn)",
                "hero_gap_report": "docs/HERO_BATCH_02_101_200_GAP_REPORT.json",
            },
            "D1_option_a_ssot": _hero_option_a_search(),
        },
        "jscpd": jscpd,
        "batch04_independent_current": 0,
        "progress_826_current": 148,
        "batch05_open": False,
        "live_gate": "AWAITING_DEPLOY per owner agreement",
    }
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
