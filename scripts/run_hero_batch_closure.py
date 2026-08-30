#!/usr/bin/env python3
"""Run hero batch 01 closure — gap analysis, live exec, evidence registry, optional xlsx upgrade."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from openpyxl import load_workbook
from openpyxl.styles import Alignment

from pdf_capability_registry import batch_test_module_for, discover_bindings, execute_capability
from scripts.upgrade_partial_capabilities import apply_to_xlsx, format_status, parse_row

BATCH_PATH = ROOT / "scripts" / "partial_batches" / "batch_hero_01.json"
EVIDENCE_PATH = ROOT / "data" / "hero_batch_01_evidence.jsonl"
GAP_REPORT = ROOT / "docs" / "HERO_BATCH_01_GAP_REPORT.json"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def load_manifest() -> dict:
    return json.loads(BATCH_PATH.read_text(encoding="utf-8"))


def gap_for(cap_id: int, binding: tuple[str, str] | None, exec_ok: bool, test_mod: str | None) -> dict:
    parts = []
    pct = 0
    if binding:
        pct += 40
    else:
        parts.append("missing dedicated _NNN binding")
    if test_mod:
        pct += 25
    else:
        parts.append("missing custom/batch test reference")
    if exec_ok:
        pct += 25
    else:
        parts.append("live execution failed")
    pct += 10  # registry row slot (updated on upgrade)
    return {
        "completion_pct": min(pct, 100),
        "missing_parts": "; ".join(parts) if parts else "—",
        "binding": f"{binding[0]}.{binding[1]}" if binding else None,
        "test_module": test_mod,
        "live_ok": exec_ok,
    }


async def run_closure(*, upgrade: bool = False, dry_run: bool = False) -> dict:
    manifest = load_manifest()
    ids = [int(x) for x in manifest["capability_ids"]]
    bindings = discover_bindings()
    rows: list[dict] = []
    ok = fail = skip = 0

    for cid in ids:
        binding = bindings.get(cid)
        test_mod = batch_test_module_for(cid) or (
            "tests/test_hero_batch_01_capabilities.py" if binding and "heroes_capability_layer" in (binding[0] if binding else "") else None
        )
        if not binding:
            skip += 1
            gap = gap_for(cid, None, False, test_mod)
            rows.append({"id": cid, "status": "skip_no_binding", **gap})
            continue
        exec_result = await execute_capability(cid)
        passed = bool(exec_result.get("ok"))
        gap = gap_for(cid, binding, passed, test_mod)
        if passed:
            ok += 1
            status = "ok"
        else:
            fail += 1
            status = "fail"
        rows.append(
            {
                "id": cid,
                "status": status,
                "binding": f"{binding[0]}.{binding[1]}",
                "exec": {k: exec_result.get(k) for k in ("ok", "error", "binding", "capability_id")},
                **gap,
            }
        )

    summary = {
        "batch": manifest.get("label"),
        "processed": len(ids),
        "ok": ok,
        "fail": fail,
        "skip_no_binding": skip,
        "timestamp": _utcnow(),
    }

    GAP_REPORT.parent.mkdir(parents=True, exist_ok=True)
    GAP_REPORT.write_text(json.dumps({"summary": summary, "capabilities": rows}, indent=2, ensure_ascii=False), encoding="utf-8")

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_PATH.open("a", encoding="utf-8") as fh:
        for row in rows:
            if row["status"] == "ok":
                fh.write(
                    json.dumps(
                        {
                            "capability_id": row["id"],
                            "binding": row["binding"],
                            "test_module": row.get("test_module"),
                            "completion_pct": row["completion_pct"],
                            "verified_at": _utcnow(),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    if upgrade and not dry_run:
        wb = load_workbook(ROOT / "capabilities_checklist.xlsx")
        upgrades: dict[int, tuple[str, str]] = {}
        for row in rows:
            if row["status"] != "ok":
                continue
            cid = row["id"]
            ev = f"{row['binding']}"
            if row.get("test_module"):
                ev += f" + {row['test_module']}"
            upgrades[cid] = ("مبني وشغال فعليًا", ev)
        if upgrades:
            apply_to_xlsx(upgrades)
        summary["xlsx_upgraded"] = len(upgrades)

    summary["gap_report"] = str(GAP_REPORT)
    summary["evidence_log"] = str(EVIDENCE_PATH)
    summary["failures"] = [r for r in rows if r["status"] != "ok"][:25]
    return summary


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upgrade", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample-report", type=int, default=0, help="Emit full dossier for N random OK capabilities")
    args = parser.parse_args()
    summary = await run_closure(upgrade=args.upgrade, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.sample_report:
        gap = json.loads(GAP_REPORT.read_text(encoding="utf-8"))
        ok_rows = [r for r in gap["capabilities"] if r["status"] == "ok"]
        sample = random.sample(ok_rows, min(args.sample_report, len(ok_rows)))
        dossier_path = ROOT / "docs" / "HERO_BATCH_01_SAMPLE_DOSSIER.json"
        dossier = []
        bindings = discover_bindings()
        for row in sample:
            cid = row["id"]
            exec_result = await execute_capability(cid)
            dossier.append(
                {
                    "capability_id": cid,
                    "gap_before_closure": row,
                    "quad_evidence": {
                        "code": row["binding"],
                        "test": row.get("test_module"),
                        "live_exec": exec_result,
                        "registry": "capabilities_checklist.xlsx + data/hero_batch_01_evidence.jsonl",
                    },
                }
            )
        dossier_path.write_text(json.dumps(dossier, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote sample dossier ({len(dossier)} caps) -> {dossier_path}")


if __name__ == "__main__":
    asyncio.run(main())
