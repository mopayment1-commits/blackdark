#!/usr/bin/env python3
"""Retrospective 4-way reclassification for batches 01–04 (400 capabilities).

Splits quad-passing capabilities into VERIFIED-DEEP (native) vs REUSED-LINK.
"""

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

from pdf_capability_registry import discover_bindings  # noqa: E402
from scripts.retrospective_deep_audit import (  # noqa: E402
    CLASSIFICATION_ORDER,
    _empty_counts,
    _load_gap_impl_classes,
    _load_ids,
    _load_prior_evidence,
    _parse_heroes_underlying,
    _update_checklist,
    _update_evidence,
    _update_gap,
    audit_capability_row,
)

BATCH_MANIFESTS = [
    ("batch_01", ROOT / "scripts/partial_batches/batch_hero_01.json"),
    ("batch_02", ROOT / "scripts/partial_batches/batch_02_101_200.json"),
    ("batch_03", ROOT / "scripts/partial_batches/batch_03_201_300.json"),
    ("batch_04", ROOT / "scripts/partial_batches/batch_04_301_400.json"),
]

EVIDENCE_PATHS = {
    "batch_01": ROOT / "data/hero_batch_01_evidence.jsonl",
    "batch_02": ROOT / "data/hero_batch_02_101_200_evidence.jsonl",
    "batch_03": ROOT / "data/hero_batch_03_201_300_evidence.jsonl",
    "batch_04": ROOT / "data/hero_batch_04_301_400_evidence.jsonl",
}

GAP_PATHS = {
    "batch_01": ROOT / "docs/HERO_BATCH_01_GAP_REPORT.json",
    "batch_02": ROOT / "docs/HERO_BATCH_02_101_200_GAP_REPORT.json",
    "batch_03": ROOT / "docs/HERO_BATCH_03_201_300_GAP_REPORT.json",
    "batch_04": ROOT / "docs/HERO_BATCH_04_301_400_GAP_REPORT.json",
}

AUDIT_JSON = ROOT / "docs/RETROSPECTIVE_RECLASSIFICATION_BATCHES_01_04.json"
AUDIT_MD = ROOT / "docs/RETROSPECTIVE_RECLASSIFICATION_BATCHES_01_04_REPORT.md"


async def reclassify_all(*, run_tests: bool = True, reuse_cached_tests: bool = True) -> dict:
    heroes_map = _parse_heroes_underlying()
    bindings = discover_bindings()

    batch_ids: dict[str, list[int]] = {}
    for batch_name, path in BATCH_MANIFESTS:
        batch_ids[batch_name] = _load_ids(path)

    prior_by_id: dict[int, dict] = {}
    gap_classes: dict[int, str] = {}
    for batch_name in batch_ids:
        for cid, row in _load_prior_evidence(EVIDENCE_PATHS[batch_name]).items():
            prior_by_id[cid] = row
        gap_classes.update(_load_gap_impl_classes(GAP_PATHS[batch_name]))

    rows: list[dict] = []
    per_batch: dict[str, dict[str, int]] = {}
    cumulative = _empty_counts()

    for batch_name, ids in batch_ids.items():
        counts = _empty_counts()
        for cap_id in ids:
            prior = prior_by_id.get(cap_id, {})
            prior_impl = (
                prior.get("implementation_class")
                or gap_classes.get(cap_id)
            )
            cached_pass = prior.get("independent_test_passed") if reuse_cached_tests else None
            row = await audit_capability_row(
                cap_id,
                batch=batch_name,
                heroes_map=heroes_map,
                bindings=bindings,
                prior_impl=prior_impl,
                run_tests=run_tests,
                cached_test_passed=cached_pass if cached_pass is True else None,
                cached_test_file=prior.get("independent_test_file") if cached_pass else None,
            )
            counts[row["classification"]] += 1
            cumulative[row["classification"]] += 1
            rows.append(row)
        per_batch[batch_name] = counts

    total = sum(len(v) for v in batch_ids.values())
    quad_total = cumulative["VERIFIED-DEEP"] + cumulative["REUSED-LINK"]
    return {
        "audit_type": "retrospective_4way_reclassification",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "total_capabilities": total,
        "classification_counts": cumulative,
        "per_batch_counts": per_batch,
        "verified_deep_native_count": cumulative["VERIFIED-DEEP"],
        "reused_link_count": cumulative["REUSED-LINK"],
        "quad_passing_total": quad_total,
        "wrapper_only_unverified_count": cumulative["WRAPPER-ONLY-UNVERIFIED"],
        "deferred_delegated_count": cumulative["DEFERRED/DELEGATED"],
        "rows": rows,
    }


def write_md(report: dict) -> None:
    c = report["classification_counts"]
    total = report["total_capabilities"]
    lines = [
        "# Retrospective 4-Way Reclassification — Batches 01–04 (400 capabilities)",
        "",
        f"**Audited at:** {report['audited_at']}",
        "",
        "## Cumulative (400 capabilities)",
        "",
        "| Classification | Count | % |",
        "|---|---:|---:|",
        f"| **VERIFIED-DEEP (native)** | **{c['VERIFIED-DEEP']}** | {round(100*c['VERIFIED-DEEP']/total,1)}% |",
        f"| **REUSED-LINK** | **{c['REUSED-LINK']}** | {round(100*c['REUSED-LINK']/total,1)}% |",
        f"| WRAPPER-ONLY-UNVERIFIED | {c['WRAPPER-ONLY-UNVERIFIED']} | {round(100*c['WRAPPER-ONLY-UNVERIFIED']/total,1)}% |",
        f"| DEFERRED/DELEGATED | {c['DEFERRED/DELEGATED']} | {round(100*c['DEFERRED/DELEGATED']/total,1)}% |",
        "",
        f"**Quad-passing total (native + reused):** {report['quad_passing_total']}",
        "",
        "## Per batch",
        "",
        "| Batch | Native | REUSED-LINK | Wrapper | Deferred |",
        "|---|---:|---:|---:|---:|",
    ]
    labels = {
        "batch_01": "01 (hero)",
        "batch_02": "02 (101–200)",
        "batch_03": "03 (201–300)",
        "batch_04": "04 (301–400)",
    }
    for batch_name, counts in report["per_batch_counts"].items():
        lines.append(
            f"| {labels[batch_name]} | {counts['VERIFIED-DEEP']} | {counts['REUSED-LINK']} | "
            f"{counts['WRAPPER-ONLY-UNVERIFIED']} | {counts['DEFERRED/DELEGATED']} |"
        )
    lines += [
        "",
        "## Method",
        "",
        "- Quad criteria unchanged (real code + independent test PASS + live OK + source traced).",
        "- REUSED-LINK: quad pass + `merged_into` / `extends_ref` / `exact_fn_reuse` / heroes delegate.",
        "",
        f"Full JSON: `{AUDIT_JSON.relative_to(ROOT)}`",
    ]
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {AUDIT_MD}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-tests", action="store_true", help="Skip per-cap pytest (faster, less strict)")
    parser.add_argument("--no-update", action="store_true", help="Do not update evidence/gap/checklist")
    args = parser.parse_args()

    print("Starting retrospective 4-way reclassification (400 capabilities)...")
    report = asyncio.run(reclassify_all(run_tests=not args.skip_tests))

    AUDIT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {AUDIT_JSON}")
    write_md(report)

    if not args.no_update:
        for batch_name, path in BATCH_MANIFESTS:
            id_set = set(_load_ids(path))
            _update_evidence(EVIDENCE_PATHS[batch_name], report["rows"], id_set)
            _update_gap(GAP_PATHS[batch_name], report["rows"], id_set, batch_name)
        _update_checklist(report["rows"])

    c = report["classification_counts"]
    print("\n=== 4-WAY HONEST COUNT (400) ===")
    for label in CLASSIFICATION_ORDER:
        print(f"{label:28} {c[label]}")
    print(f"{'Quad-passing total':28} {report['quad_passing_total']}")
  # noqa: E501
    print("\n=== PER BATCH ===")
    for batch_name, counts in report["per_batch_counts"].items():
        print(
            f"{batch_name}: native={counts['VERIFIED-DEEP']} reused={counts['REUSED-LINK']} "
            f"wrapper={counts['WRAPPER-ONLY-UNVERIFIED']} deferred={counts['DEFERRED/DELEGATED']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
