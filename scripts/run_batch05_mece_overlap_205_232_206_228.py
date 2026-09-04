#!/usr/bin/env python3
"""Priority MECE + Type-4 gate for Batch05 pairs #205↔#232 and #206↔#228."""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BATCH05_MECE_OVERLAP_205_232_206_228_DECISION.json"
SYMBOLS = ["BTC", "ETH", "SOL", "AVAX", "DOGE"]


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


async def _probe_canonical(capability_id: int, symbol: str) -> dict[str, Any]:
    from cap646.batch02_production import execute as batch02_execute
    from cap646.batch05_dedicated import execute as batch05_execute
    from cap646.runtime import execute_capability

    if capability_id in {206, 228}:
        canonical = await batch02_execute(86, params={"symbol": symbol})
        canonical_spine = "batch02"
    elif capability_id == 232:
        canonical = await batch05_execute(205, params={"symbol": symbol})
        canonical_spine = "batch05_canonical_205"
    else:
        canonical = await batch05_execute(capability_id, params={"symbol": symbol})
        canonical_spine = "batch05"

    hero = await batch05_execute(capability_id, params={"symbol": symbol})
    runtime = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": symbol})

    return {
        "symbol": symbol,
        "canonical_spine": canonical_spine,
        "canonical_surface": canonical.get("surface"),
        "canonical_success": canonical.get("success"),
        "runtime_spine": runtime.get("production_spine"),
        "runtime_surface": runtime.get("surface"),
        "hero_surface": hero.get("surface"),
        "hero_domain_keys": list((hero.get(hero.get("surface")) or {}).keys())[:10],
    }


async def build() -> dict[str, Any]:
    pairs: list[dict[str, Any]] = [
        {
            "pair": "205_232",
            "capability_id": 205,
            "duplicate_id": 232,
            "catalog_capability": "Open Interest Intelligence",
            "official_batch": "batch05",
            "canonical_capability_id": 205,
            "canonical_spine": "batch05",
            "canonical_binding": "cap646/batch05_dedicated.py::_cap205",
            "duplicate_binding": "cap646/batch05_dedicated.py::_cap232 → facade _cap205",
            "hero_bindings_audited": [
                {
                    "id": 205,
                    "path": "bd_platform.onchain_defi_sources_layer.ingest_glassnode_metrics_205",
                    "payload_domain": "glassnode_metrics",
                    "semantic_match_catalog": False,
                    "note": "Static seed metrics — not live OI; brownfield Invest input",
                },
                {
                    "id": 232,
                    "path": "bd_platform.intelligence_ux_extensions_layer.attach_arbitrage_comparison_230_232",
                    "payload_domain": "arbitrage_comparison",
                    "semantic_match_catalog": False,
                },
            ],
            "type4_per_symbol": {},
            "mece_verdict": "INTERNAL_DUPLICATE — #232 catalog duplicate of canonical #205 (REPEAT_CANONICAL); hero #232 is Type-4 SPLIT-BRAIN",
            "time_decision_canonical": "Invest",
            "time_decision_duplicate": "Migrate",
            "closure_status_canonical": "NOT_COMPLETE",
            "closure_status_duplicate": "REUSED-LINK",
            "hero_action": "Eliminate #232 arbitrage hero from production — facade to _cap205 only",
            "adr": "docs/ADR_BATCH05_232_REUSED_LINK_205.md",
        },
        {
            "pair": "206_228",
            "capability_id": 206,
            "duplicate_id": 228,
            "catalog_capability": "Funding Rate Intelligence",
            "official_batch": "batch05",
            "canonical_capability_id": 86,
            "canonical_spine": "batch02",
            "canonical_binding": "cap646/batch02_production.py::cap_086 → cap646.batch02_dedicated._cap086",
            "duplicate_binding": "cap646/batch05_dedicated.py::_cap206/_cap228 → facade batch02 #86",
            "hero_bindings_audited": [
                {
                    "id": 206,
                    "path": "bd_platform.onchain_defi_sources_layer.ingest_uniswap_subgraph_206",
                    "payload_domain": "uniswap_subgraph",
                    "semantic_match_catalog": False,
                },
                {
                    "id": 228,
                    "path": "bd_platform.intelligence_ux_extensions_layer.simulate_drawdown_hedge_228",
                    "payload_domain": "drawdown_hedge_simulation",
                    "semantic_match_catalog": False,
                },
            ],
            "type4_per_symbol": {},
            "mece_verdict": "CROSS_BATCH_DUPLICATE — both #206/#228 canonical to batch02 #86; batch02 derivatives_hub funding_rate is closer to catalog intent",
            "time_decision_canonical": "Migrate",
            "time_decision_duplicate": "Migrate",
            "closure_status_canonical": "REUSED-LINK",
            "closure_status_duplicate": "REUSED-LINK",
            "hero_action": "Eliminate uniswap/drawdown hero paths — facade to batch02 #86 only",
            "adr": "docs/ADR_BATCH05_206_228_REUSED_LINK_BATCH02.md",
        },
    ]

    for pair in pairs:
        for sym in SYMBOLS:
            for cid in (pair["capability_id"], pair["duplicate_id"]):
                key = f"{cid}_{sym}"
                pair["type4_per_symbol"][key] = await _probe_canonical(cid, sym)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "commit_hash": git_commit(),
        "scope": "Priority MECE + Type-4 — Batch05 pairs #205↔#232 (OI) and #206↔#228 (Funding)",
        "symbols_tested": SYMBOLS,
        "type4_contract": "Side-by-side: canonical spine vs batch05 hero binding per symbol",
        "pairs": pairs,
    }


def main() -> None:
    doc = asyncio.run(build())
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
