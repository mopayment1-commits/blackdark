#!/usr/bin/env python3
"""Batch 04 (301-400) deep closure: live exec, quad audit, registry updates."""

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
    _classify,
    _git_on_main,
    _load_gap_impl_classes,
    _load_ids,
    _parse_heroes_underlying,
    _resolve_binding,
    _run_independent_test,
    _scan_independent_tests,
    _underlying_real_code,
    _update_checklist,
    _update_evidence,
    _update_gap,
)
from scripts.retrospective_deep_audit import _binding_from_live, _live_verify  # noqa: E402
from scripts.run_hero_batch_closure import classify_implementation, run_closure  # noqa: E402
from pdf_capability_registry import discover_bindings  # noqa: E402

BATCH_MANIFEST = ROOT / "scripts/partial_batches/batch_04_301_400.json"
EVIDENCE = ROOT / "data/hero_batch_04_301_400_evidence.jsonl"
GAP = ROOT / "docs/HERO_BATCH_04_301_400_GAP_REPORT.json"
AUDIT_JSON = ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_04_301_400.json"
AUDIT_MD = ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_04_REPORT.md"
SAMPLE_DOSSIER = ROOT / "docs/HERO_BATCH_04_SAMPLE_DOSSIER.json"


async def audit_batch04() -> dict:
    ids = _load_ids(BATCH_MANIFEST)
    heroes_map = _parse_heroes_underlying()
    bindings = discover_bindings()
    gap_classes = _load_gap_impl_classes(GAP) if GAP.is_file() else {}

    rows = []
    counts = {"VERIFIED-DEEP": 0, "WRAPPER-ONLY-UNVERIFIED": 0, "DEFERRED/DELEGATED": 0}

    for cap_id in ids:
        prior_impl = gap_classes.get(cap_id)
        module, func_name, binding_kind = _resolve_binding(cap_id, heroes_map, bindings)
        live_ok, live_detail = await _live_verify(cap_id)
        reg_binding = bindings.get(cap_id)
        if reg_binding:
            impl_guess = classify_implementation(cap_id, reg_binding, live_detail)
            if impl_guess != "deferred":
                prior_impl = prior_impl or impl_guess

        live_binding = live_detail.get("binding", "")
        if live_binding:
            lm, lf = _binding_from_live(live_binding)
            if lm and lf and not lm.endswith("heroes_capability_layer"):
                module, func_name = lm, lf
                if binding_kind == "heroes_wrapper":
                    binding_kind = "heroes_wrapper_traced"

        real, real_reason = _underlying_real_code(module, func_name)
        has_test, test_file, test_pat = _scan_independent_tests(cap_id, module, func_name)
        test_passed = False
        test_output = ""
        if has_test and test_file:
            test_passed, test_output = _run_independent_test(test_file, cap_id, func_name)

        mod_path = module.replace(".", "/") + ".py" if module else ""
        on_main = _git_on_main(mod_path) if mod_path and (ROOT / mod_path).exists() else False
        source_branch = "origin/main" if on_main else "capabilities-826-import"

        classification = _classify(
            cap_id, real, real_reason, has_test, test_passed, live_ok,
            binding_kind, prior_impl, live_detail,
        )
        counts[classification] += 1
        rows.append({
            "capability_id": cap_id,
            "batch": "batch_04",
            "classification": classification,
            "prior_implementation_class": prior_impl,
            "binding_kind": binding_kind,
            "underlying_module": module,
            "underlying_function": func_name,
            "underlying_real_code": real,
            "underlying_real_reason": real_reason,
            "independent_test_file": test_file,
            "independent_test_pattern": test_pat,
            "independent_test_passed": test_passed,
            "live_ok": live_ok,
            "source_branch": source_branch,
        })

    total = len(ids)
    return {
        "audit_type": "batch_04_deep_quad",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "total_capabilities": total,
        "classification_counts": counts,
        "verified_deep_honest_count": counts["VERIFIED-DEEP"],
        "verified_deep_pct": round(100.0 * counts["VERIFIED-DEEP"] / total, 1),
        "wrapper_only_unverified_count": counts["WRAPPER-ONLY-UNVERIFIED"],
        "deferred_delegated_count": counts["DEFERRED/DELEGATED"],
        "rows": rows,
    }


def write_md(report: dict) -> None:
    c = report["classification_counts"]
    total = report["total_capabilities"]
    deferred = [r for r in report["rows"] if r["classification"] == "DEFERRED/DELEGATED"]
    lines = [
        "# Retrospective Deep Audit — Batch 04 (301–400)",
        "",
        f"**Audited at:** {report['audited_at']}",
        "",
        "## Honest Count (100 capabilities)",
        "",
        "| Classification | Count | % |",
        "|---|---:|---:|",
        f"| **VERIFIED-DEEP** | **{c['VERIFIED-DEEP']}** | {report['verified_deep_pct']}% |",
        f"| WRAPPER-ONLY-UNVERIFIED | {c['WRAPPER-ONLY-UNVERIFIED']} | {round(100*c['WRAPPER-ONLY-UNVERIFIED']/total,1)}% |",
        f"| DEFERRED/DELEGATED | {c['DEFERRED/DELEGATED']} | {round(100*c['DEFERRED/DELEGATED']/total,1)}% |",
        "",
        "## DEFERRED/DELEGATED (documented deferrals only)",
        "",
    ]
    for r in deferred:
        lines.append(
            f"- #{r['capability_id']}: `{r['underlying_module']}.{r['underlying_function']}`"
        )
    lines += [
        "",
        "## Acceptance",
        "",
        "- WRAPPER-ONLY-UNVERIFIED = **0**",
        "- Batch 05 **blocked** until explicit user approval.",
        "",
        f"Full JSON: `{AUDIT_JSON.relative_to(ROOT)}`",
        f"Sample dossier: `{SAMPLE_DOSSIER.relative_to(ROOT)}`",
    ]
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sample_dossier(report: dict) -> None:
    import random

    verified = [r for r in report["rows"] if r["classification"] == "VERIFIED-DEEP"]
    sample = random.Random(40400).sample(verified, min(10, len(verified)))
    dossier = {
        "batch": "batch_04_301_400",
        "sample_size": len(sample),
        "selection_seed": 40400,
        "capabilities": sample,
    }
    SAMPLE_DOSSIER.write_text(json.dumps(dossier, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-closure", action="store_true")
    parser.add_argument("--skip-upgrade", action="store_true")
    args = parser.parse_args()

    if not args.skip_closure:
        print("Running batch 04 closure (live exec + gap report)...")
        summary = await run_closure("batch_04_301_400", upgrade=not args.skip_upgrade)
        print(json.dumps({k: summary[k] for k in ("live_ok", "live_fail", "implemented_native", "delegated", "deferred")}, indent=2))

    print("Running batch 04 deep quad audit...")
    report = await audit_batch04()
    AUDIT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    id_set = set(_load_ids(BATCH_MANIFEST))
    _update_evidence(EVIDENCE, report["rows"], id_set)
    _update_gap(GAP, report["rows"], id_set, "batch_04_301_400")
    _update_checklist(report["rows"])
    write_md(report)
    write_sample_dossier(report)

    c = report["classification_counts"]
    print("\n=== BATCH 04 HONEST COUNT ===")
    print(f"VERIFIED-DEEP:              {c['VERIFIED-DEEP']} / 100")
    print(f"WRAPPER-ONLY-UNVERIFIED:    {c['WRAPPER-ONLY-UNVERIFIED']} / 100")
    print(f"DEFERRED/DELEGATED:         {c['DEFERRED/DELEGATED']} / 100")
    if c["WRAPPER-ONLY-UNVERIFIED"] > 0:
        print("BLOCKED: resolve WRAPPER-ONLY before claiming batch close")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
