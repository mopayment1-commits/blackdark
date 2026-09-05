#!/usr/bin/env python3
"""Batch 05 (401-500) deep closure: live exec, quad audit, REUSED-LINK tagging."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.retrospective_deep_audit import (  # noqa: E402
    _empty_counts,
    _load_gap_impl_classes,
    _load_ids,
    _parse_heroes_underlying,
    _update_checklist,
    _update_evidence,
    _update_gap,
    audit_capability_row,
)
from scripts.run_hero_batch_closure import run_closure  # noqa: E402
from pdf_capability_registry import discover_bindings  # noqa: E402

BATCH_MANIFEST = ROOT / "scripts/partial_batches/batch_05_401_500.json"
EVIDENCE = ROOT / "data/hero_batch_05_401_500_evidence.jsonl"
GAP = ROOT / "docs/HERO_BATCH_05_401_500_GAP_REPORT.json"
AUDIT_JSON = ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_05_401_500.json"
AUDIT_MD = ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_05_REPORT.md"
SAMPLE_DOSSIER = ROOT / "docs/HERO_BATCH_05_SAMPLE_DOSSIER.json"


async def audit_batch05() -> dict:
    ids = _load_ids(BATCH_MANIFEST)
    heroes_map = _parse_heroes_underlying()
    bindings = discover_bindings()
    gap_classes = _load_gap_impl_classes(GAP) if GAP.is_file() else {}

    rows = []
    counts = _empty_counts()

    for cap_id in ids:
        row = await audit_capability_row(
            cap_id,
            batch="batch_05",
            heroes_map=heroes_map,
            bindings=bindings,
            prior_impl=gap_classes.get(cap_id),
        )
        counts[row["classification"]] += 1
        rows.append({
            "capability_id": row["capability_id"],
            "batch": row["batch"],
            "classification": row["classification"],
            "prior_implementation_class": row["prior_implementation_class"],
            "binding_kind": row["binding_kind"],
            "underlying_module": row["underlying_module"],
            "underlying_function": row["underlying_function"],
            "underlying_real_code": row["underlying_real_code"],
            "underlying_real_reason": row["underlying_real_reason"],
            "independent_test_file": row["independent_test_file"],
            "independent_test_pattern": row["independent_test_pattern"],
            "independent_test_passed": row["independent_test_passed"],
            "live_ok": row["live_ok"],
            "reuse_link": row.get("reuse_link", False),
            "reuse_meta": row.get("reuse_meta", {}),
            "source_branch": row["source_branch"],
        })

    total = len(ids)
    quad = counts["VERIFIED-DEEP"] + counts["REUSED-LINK"]
    return {
        "audit_type": "batch_05_deep_quad",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "total_capabilities": total,
        "classification_counts": counts,
        "verified_deep_native_count": counts["VERIFIED-DEEP"],
        "reused_link_count": counts["REUSED-LINK"],
        "verified_deep_honest_count": quad,
        "verified_deep_pct": round(100.0 * quad / total, 1),
        "wrapper_only_unverified_count": counts["WRAPPER-ONLY-UNVERIFIED"],
        "deferred_delegated_count": counts["DEFERRED/DELEGATED"],
        "rows": rows,
    }


def write_md(report: dict) -> None:
    c = report["classification_counts"]
    total = report["total_capabilities"]
    lines = [
        "# Retrospective Deep Audit — Batch 05 (401–500)",
        "",
        f"**Audited at:** {report['audited_at']}",
        "",
        "## Honest Count (100 capabilities)",
        "",
        "| Classification | Count | % |",
        "|---|---:|---:|",
        f"| **VERIFIED-DEEP (native)** | **{c['VERIFIED-DEEP']}** | {round(100*c['VERIFIED-DEEP']/total,1)}% |",
        f"| **REUSED-LINK** | **{c['REUSED-LINK']}** | {round(100*c['REUSED-LINK']/total,1)}% |",
        f"| WRAPPER-ONLY-UNVERIFIED | {c['WRAPPER-ONLY-UNVERIFIED']} | {round(100*c['WRAPPER-ONLY-UNVERIFIED']/total,1)}% |",
        f"| DEFERRED/DELEGATED | {c['DEFERRED/DELEGATED']} | {round(100*c['DEFERRED/DELEGATED']/total,1)}% |",
        "",
        f"Quad-passing total: **{report['verified_deep_honest_count']}**",
        "",
        f"Full JSON: `{AUDIT_JSON.relative_to(ROOT)}`",
        f"Sample dossier: `{SAMPLE_DOSSIER.relative_to(ROOT)}`",
    ]
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sample_dossier(report: dict) -> None:
    import random

    quad_pass = [r for r in report["rows"] if r["classification"] in ("VERIFIED-DEEP", "REUSED-LINK")]
    sample = random.Random(50500).sample(quad_pass, min(10, len(quad_pass)))
    dossier = {
        "batch": "batch_05_401_500",
        "sample_size": len(sample),
        "selection_seed": 50500,
        "capabilities": sample,
    }
    SAMPLE_DOSSIER.write_text(json.dumps(dossier, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-closure", action="store_true")
    parser.add_argument("--skip-upgrade", action="store_true")
    args = parser.parse_args()

    if not args.skip_closure:
        print("Running batch 05 closure (live exec + gap report)...")
        summary = await run_closure("batch_05_401_500", upgrade=not args.skip_upgrade)
        print(json.dumps({k: summary[k] for k in ("live_ok", "live_fail", "implemented_native", "delegated", "deferred")}, indent=2))

    print("Running batch 05 deep quad audit...")
    report = await audit_batch05()
    AUDIT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    id_set = set(_load_ids(BATCH_MANIFEST))
    _update_evidence(EVIDENCE, report["rows"], id_set)
    _update_gap(GAP, report["rows"], id_set, "batch_05_401_500")
    _update_checklist(report["rows"])
    write_md(report)
    write_sample_dossier(report)

    c = report["classification_counts"]
    print("\n=== BATCH 05 HONEST COUNT ===")
    print(f"VERIFIED-DEEP (native):     {c['VERIFIED-DEEP']} / 100")
    print(f"REUSED-LINK:                {c['REUSED-LINK']} / 100")
    print(f"WRAPPER-ONLY-UNVERIFIED:    {c['WRAPPER-ONLY-UNVERIFIED']} / 100")
    print(f"DEFERRED/DELEGATED:         {c['DEFERRED/DELEGATED']} / 100")
    if c["WRAPPER-ONLY-UNVERIFIED"] > 0:
        print("BLOCKED: resolve WRAPPER-ONLY before claiming batch close")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
