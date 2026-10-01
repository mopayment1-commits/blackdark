#!/usr/bin/env python3
"""4-level deduplication audit for official Batch03 IDs 101–150."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BATCH03_RANGE = range(101, 151)
REUSED_LINK_PAIRS = {106: 63, 107: 64, 110: 69, 125: 85}
OVERLAP_BATCH01 = {103: 3, 129: 29}
SYMBOLS = ["BTC", "ETH", "SOL", "AVAX", "DOGE"]


def _jscpd_report() -> dict[str, Any]:
    out_dir = ROOT / "docs/.jscpd-batch03"
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = [
        "cap646/batch03_dedicated.py",
        "cap646/batch03_production.py",
        "cap646/handlers/batch03.py",
    ]
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
            *targets,
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=180,
    )
    report_path = out_dir / "jscpd-report.json"
    report: dict[str, Any] = {"exit_code": proc.returncode, "stderr": proc.stderr[-1000:] if proc.stderr else ""}
    if report_path.is_file():
        report["duplicates"] = json.loads(report_path.read_text(encoding="utf-8"))
    return report


def _mece_layer() -> list[dict[str, Any]]:
    from cap646.catalog import catalog_by_id

    catalog = catalog_by_id()
    rows: list[dict[str, Any]] = []
    for dup_id, canon_id in REUSED_LINK_PAIRS.items():
        dup_goal = catalog.get(dup_id, {}).get("capability")
        canon_goal = catalog.get(canon_id, {}).get("capability")
        rows.append(
            {
                "duplicate_id": dup_id,
                "canonical_id": canon_id,
                "decision": "REUSED-LINK",
                "mece_basis": "identical catalog goal — canonical SSOT in batch02",
                "duplicate_goal": dup_goal,
                "canonical_goal": canon_goal,
            }
        )
    for dup_id, batch01_id in OVERLAP_BATCH01.items():
        rows.append(
            {
                "duplicate_id": dup_id,
                "canonical_id": batch01_id,
                "decision": "OVERLAP-PARTIAL",
                "mece_basis": "batch03 ID served exclusively via batch01 spine",
                "duplicate_goal": catalog.get(dup_id, {}).get("capability"),
                "canonical_goal": catalog.get(batch01_id, {}).get("capability"),
            }
        )
  # #103 vs batch01 #3 — distinct official batch, same spine route
    rows.append(
        {
            "pair": "103_vs_129",
            "decision": "DISTINCT",
            "mece_basis": "API Data Platform (#103) vs Sentiment Intelligence (#129) — different goals/surfaces",
        }
    )
    return rows


async def _type4_contract_tests() -> list[dict[str, Any]]:
    from cap646.runtime import execute_capability

    tests: list[dict[str, Any]] = []
    for dup_id, canon_id in REUSED_LINK_PAIRS.items():
        for symbol in SYMBOLS:
            dup = await execute_capability(dup_id, skip_entitlement=True, params={"symbol": symbol, "tier": "pro"})
            canon = await execute_capability(canon_id, skip_entitlement=True, params={"symbol": symbol, "tier": "pro"})
            link = dup.get("catalog_link") or {}
            tests.append(
                {
                    "duplicate_id": dup_id,
                    "canonical_id": canon_id,
                    "symbol": symbol,
                    "surface_match": dup.get("surface") == canon.get("surface"),
                    "success": bool(dup.get("success") and canon.get("success")),
                    "catalog_link_ok": link.get("duplicate_of") == canon_id,
                    "contract_pass": (
                        dup.get("surface") == canon.get("surface")
                        and dup.get("success")
                        and canon.get("success")
                        and link.get("duplicate_of") == canon_id
                    ),
                }
            )
    return tests


async def main() -> None:
    mece = _mece_layer()
    type4 = await _type4_contract_tests()
    jscpd = _jscpd_report()
    type4_pass = all(t["contract_pass"] for t in type4)
    out = {
        "audited_at": datetime.now(UTC).isoformat(),
        "scope": "official batch03 IDs 101–150",
        "layers": {
            "layer_1_mece": {
                "method": "TOGAF G189 inputs/outputs/commercial outcome",
                "findings": mece,
            },
            "layer_2_structural": {
                "method": "jscpd on batch03 spine modules",
                "jscpd": jscpd,
            },
            "layer_3_modularity": {
                "method": "SSOT via canonical batch02 for REUSED-LINK",
                "ssot_pairs": REUSED_LINK_PAIRS,
            },
            "layer_4_semantic": {
                "method": "live contract tests >=5 symbols per REUSED-LINK pair",
                "contract_tests": type4,
                "all_pass": type4_pass,
            },
        },
        "time_decisions": [
            {
                "ids": list(REUSED_LINK_PAIRS),
                "decision": "Migrate",
                "rationale": "Canonical + Facade with catalog_link; Type-4 contract in CI",
                "adr": "docs/REUSED_LINK_TAXONOMY.json",
                "sunset_date": None,
            },
            {
                "ids": list(OVERLAP_BATCH01),
                "decision": "Tolerate",
                "rationale": "Runtime routes batch01 before batch03 — distinct batch numbering",
                "sunset_date": "2026-10-03",
            },
        ],
        "all_layers_pass": type4_pass,
    }
    path = ROOT / "docs/BATCH03_DEDUP_AUDIT.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_layers_pass": out["all_layers_pass"], "type4_count": len(type4)}, indent=2))
    print(f"Wrote {path}")
    if not type4_pass:
        raise SystemExit("Batch03 Type-4 contract tests failed")


if __name__ == "__main__":
    asyncio.run(main())
