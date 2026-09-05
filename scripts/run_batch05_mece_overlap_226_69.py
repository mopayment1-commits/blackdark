#!/usr/bin/env python3
"""Priority MECE + Type-4 gate for Batch05 pair #226↔#69."""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BATCH05_MECE_OVERLAP_226_69_DECISION.json"
SYMBOLS = ["BTC", "ETH", "SOL", "AVAX", "DOGE"]


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


async def _probe(capability_id: int, symbol: str) -> dict[str, Any]:
    from cap646.batch02_production import execute as batch02_execute
    from cap646.batch05_production import execute as batch05_execute
    from cap646.runtime import execute_capability

    canonical = await batch02_execute(69, params={"symbol": symbol})
    hero = await batch05_execute(capability_id, params={"symbol": symbol})
    runtime = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": symbol})

    return {
        "symbol": symbol,
        "canonical_spine": "batch02",
        "canonical_surface": canonical.get("surface"),
        "canonical_success": canonical.get("success"),
        "runtime_spine": runtime.get("production_spine"),
        "runtime_surface": runtime.get("surface"),
        "facade_surface": hero.get("surface"),
        "facade_classification": hero.get("classification"),
        "canonical_has_cross_domain": "cross_domain_decision" in (canonical or {}),
    }


async def build() -> dict[str, Any]:
    pair = {
        "pair": "226_69",
        "capability_id": 226,
        "duplicate_id": 226,
        "catalog_capability": "Cross-Domain Decision Intelligence Layer",
        "official_batch": "batch05",
        "canonical_capability_id": 69,
        "canonical_spine": "batch02",
        "canonical_binding": "cap646/batch02_production.py::cap_069 → cap646.batch02_dedicated._cap069",
        "duplicate_binding": "cap646/batch05_dedicated.py::_cap226 → facade batch02 #69",
        "hero_bindings_audited": [
            {
                "id": 226,
                "path": "bd_platform.intelligence_market_extensions_layer.analyze_launch_event_226",
                "payload_domain": "launch_event_analysis",
                "semantic_match_catalog": False,
            }
        ],
        "type4_per_symbol": {},
        "mece_verdict": "CROSS_BATCH_DUPLICATE — #226 canonical to batch02 #69; hero launch-event is Type-4 SPLIT-BRAIN",
        "time_decision_canonical": "Invest",
        "time_decision_duplicate": "Migrate",
        "closure_status_canonical": "NOT_COMPLETE",
        "closure_status_duplicate": "REUSED-LINK",
        "hero_action": "Eliminate launch-event hero — facade to batch02 #69 only",
        "adr": "docs/ADR_BATCH05_226_REUSED_LINK_BATCH02.md",
    }
    for sym in SYMBOLS:
        pair["type4_per_symbol"][f"226_{sym}"] = await _probe(226, sym)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "commit_hash": git_commit(),
        "scope": "Priority MECE + Type-4 — Batch05 pair #226↔#69 (Cross-Domain Decision)",
        "symbols_tested": SYMBOLS,
        "pairs": [pair],
    }


def main() -> None:
    doc = asyncio.run(build())
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
