#!/usr/bin/env python3
"""Run capability batch closure — gap analysis, live exec, proof hashes, deferred/delegated tags."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pdf_capability_registry import batch_test_module_for, discover_bindings, execute_capability
from scripts.upgrade_partial_capabilities import apply_to_xlsx

BATCH_DIR = ROOT / "scripts" / "partial_batches"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def load_manifest(batch_name: str) -> dict:
    path = BATCH_DIR / f"{batch_name}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def proof_hash(exec_result: dict[str, Any]) -> str:
    stable = {k: v for k, v in exec_result.items() if k not in {"verified_at", "timestamp"}}
    payload = json.dumps(stable, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def classify_implementation(
    capability_id: int,
    registry_binding: tuple[str, str],
    exec_result: dict[str, Any],
) -> str:
    """implemented | delegated | deferred"""
    reg = f"{registry_binding[0]}.{registry_binding[1]}"
    live = str(exec_result.get("binding") or "")
    blob = json.dumps(exec_result, default=str).lower()

    deferred_markers = (
        "deferred",
        "rejected",
        "duplicate_not_build",
        "build_blocked",
        "wave 3",
        "insights_only_no_execution",
    )
    if any(m in blob for m in deferred_markers) or exec_result.get("status") in {"deferred", "rejected"}:
        return "deferred"

  # noqa: E501
    if (
        "heroes_capability_layer" in reg
        and live
        and live != reg
        and not live.endswith(registry_binding[1])
    ):
        return "delegated"
    if exec_result.get("extends_ref") or exec_result.get("merged_into") or exec_result.get("duplicate_of"):
        if capability_id != int(exec_result.get("feature_ref") or capability_id):
            return "delegated"
    if live and live != reg:
        return "delegated"
    return "implemented"


def gap_for(
    cap_id: int,
    binding: tuple[str, str] | None,
    exec_ok: bool,
    test_mod: str | None,
    impl_class: str,
) -> dict[str, Any]:
    parts: list[str] = []
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
    if impl_class == "implemented":
        pct += 10
    elif impl_class == "delegated":
        parts.append("delegated — not counted as native implementation")
        pct += 5
    else:
        parts.append("deferred — not counted as native implementation")
        pct += 0
    return {
        "completion_pct": min(pct, 100),
        "missing_parts": "; ".join(parts) if parts else "—",
        "binding": f"{binding[0]}.{binding[1]}" if binding else None,
        "test_module": test_mod,
        "live_ok": exec_ok,
        "implementation_class": impl_class,
    }


def test_module_for(capability_id: int, batch_name: str) -> str | None:
    mod = batch_test_module_for(capability_id)
    if mod and (ROOT / mod).is_file():
        return mod
    if batch_name.startswith("batch_02"):
        return "tests/test_hero_batch_02_capabilities.py"
    if batch_name.startswith("batch_hero_01"):
        return "tests/test_hero_batch_01_capabilities.py"
    return mod


async def run_closure(
    batch_name: str,
    *,
    upgrade: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    manifest = load_manifest(batch_name)
    ids = [int(x) for x in manifest["capability_ids"]]
    bindings = discover_bindings()

    batch_slug = batch_name.replace("batch_", "").replace("-", "_")
    gap_report = ROOT / "docs" / f"HERO_BATCH_{batch_slug.upper()}_GAP_REPORT.json"
    evidence_path = ROOT / "data" / f"hero_batch_{batch_slug}_evidence.jsonl"

    rows: list[dict] = []
    ok = fail = skip = 0
    implemented = delegated = deferred = 0

    for cid in ids:
        binding = bindings.get(cid)
        test_mod = test_module_for(cid, batch_name)
        if not binding:
            skip += 1
            gap = gap_for(cid, None, False, test_mod, "missing")
            rows.append({"id": cid, "status": "skip_no_binding", **gap})
            continue

        exec_result = await execute_capability(cid)
        passed = bool(exec_result.get("ok"))
        impl_class = classify_implementation(cid, binding, exec_result)
        phash = proof_hash(exec_result)
        verified_at = _utcnow()

        if impl_class == "implemented":
            implemented += 1
        elif impl_class == "delegated":
            delegated += 1
        else:
            deferred += 1

        gap = gap_for(cid, binding, passed, test_mod, impl_class)
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
                "implementation_class": impl_class,
                "proof_hash": phash,
                "verified_at": verified_at,
                "exec": {
                    k: exec_result.get(k)
                    for k in ("ok", "error", "binding", "capability_id", "status", "extends_ref", "merged_into")
                },
                **gap,
            }
        )

    summary = {
        "batch": manifest.get("label"),
        "processed": len(ids),
        "live_ok": ok,
        "live_fail": fail,
        "skip_no_binding": skip,
        "implemented_native": implemented,
        "delegated": delegated,
        "deferred": deferred,
        "timestamp": _utcnow(),
    }

    gap_report.parent.mkdir(parents=True, exist_ok=True)
    gap_report.write_text(json.dumps({"summary": summary, "capabilities": rows}, indent=2, ensure_ascii=False), encoding="utf-8")

    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            if row["status"] != "ok":
                continue
            fh.write(
                json.dumps(
                    {
                        "capability_id": row["id"],
                        "binding": row["binding"],
                        "implementation_class": row["implementation_class"],
                        "test_module": row.get("test_module"),
                        "completion_pct": row["completion_pct"],
                        "proof_hash": row["proof_hash"],
                        "verified_at": row["verified_at"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    if upgrade and not dry_run:
        upgrades: dict[int, tuple[str, str]] = {}
        for row in rows:
            if row["status"] != "ok":
                continue
            tag = row["implementation_class"]
            cid = row["id"]
            ev = f"[{tag}] {row['binding']}"
            if row.get("test_module"):
                ev += f" + {row['test_module']}"
            ev += f" | proof={row['proof_hash'][:16]}"
            if tag == "implemented":
                upgrades[cid] = ("مبني وشغال فعليًا", ev)
            elif tag == "delegated":
                upgrades[cid] = ("مبني جزئيًا", ev + " (delegated)")
            else:
                upgrades[cid] = ("مبني جزئيًا", ev + " (deferred)")
        if upgrades:
            apply_to_xlsx(upgrades)
        summary["xlsx_upgraded"] = len(upgrades)

    summary["gap_report"] = str(gap_report)
    summary["evidence_log"] = str(evidence_path)
    summary["failures"] = [r for r in rows if r["status"] != "ok"][:25]
    return summary


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", help="Manifest name without .json (e.g. batch_02_101_200)")
    parser.add_argument("--upgrade", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample-report", type=int, default=0)
    args = parser.parse_args()
    summary = await run_closure(args.batch, upgrade=args.upgrade, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.sample_report:
        batch_slug = args.batch.replace("batch_", "").replace("-", "_")
        gap_report = ROOT / "docs" / f"HERO_BATCH_{batch_slug.upper()}_GAP_REPORT.json"
        gap = json.loads(gap_report.read_text(encoding="utf-8"))
        ok_rows = [r for r in gap["capabilities"] if r["status"] == "ok"]
        sample = random.sample(ok_rows, min(args.sample_report, len(ok_rows)))
        dossier_path = ROOT / "docs" / f"HERO_BATCH_{batch_slug.upper()}_SAMPLE_DOSSIER.json"
        dossier = []
        for row in sample:
            cid = row["id"]
            exec_result = await execute_capability(cid)
            dossier.append(
                {
                    "capability_id": cid,
                    "implementation_class": row["implementation_class"],
                    "proof_hash": row["proof_hash"],
                    "verified_at": row["verified_at"],
                    "quad_evidence": {
                        "code": row["binding"],
                        "test": row.get("test_module"),
                        "live_exec": exec_result,
                        "registry": f"capabilities_checklist.xlsx + data/hero_batch_{batch_slug}_evidence.jsonl",
                    },
                }
            )
        dossier_path.write_text(json.dumps(dossier, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote sample dossier ({len(dossier)} caps) -> {dossier_path}")


if __name__ == "__main__":
    asyncio.run(main())
