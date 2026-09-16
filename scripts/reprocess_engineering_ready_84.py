#!/usr/bin/env python3
"""Re-process the 84 ENGINEERING_READY register rows — no full 826 rebuild."""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BUILD_DIR = ROOT / "institutional_due_diligence_2026/CAPABILITY_BUILD_826"
REGISTER_PATH = BUILD_DIR / "CAPABILITY_REGISTER.json"
PROGRESS_LOG = BUILD_DIR / "BUILD_PROGRESS.log"
PYTHON = str(ROOT / ".venv/bin/python")

from scripts.capability_build_826_executor import (  # noqa: E402
    _core_gates_clean,
    _git_sha,
    audit_ids,
    load_register,
    runtime_probe,
    write_heroes_binding_index,
)
from scripts.audit_standards_v6 import discover_ai_cap_ids, phase3_ai_rmf_plus_218a  # noqa: E402


def _now() -> str:
    return datetime.now(UTC).isoformat()


def gate_label(failure: str) -> str:
    mapping = {
        "v6_13.8_performance_gate": "v6 §2.1 / Phase 2 GIPS — performance gate (decision-ledger unverifiable)",
        "evidence_pack.8_reliability_performance_evidence": "v6 evidence pack §8 — reliability/performance (GIPS phase 2)",
        "ai_rmf_800_218a_applied": "v6 §2.1 / Phase 3 — NIST AI RMF + SP 800-218A",
        "v6_13.1_functional_completeness": "v6 §2.1 criterion 1 — functional completeness (Phase 7 SRE snapshot)",
        "v6_13.5_integration_correctness": "v6 §2.1 criterion 5 — integration (Phase 5 COSO snapshot)",
        "v6_13.9_reliability_gate": "v6 §2.1 criterion 9 — reliability (Phase 8 SRE snapshot)",
        "v6_13.10_observability_gate": "v6 §2.1 criterion 10 — observability (Phase 8 SRE snapshot)",
    }
    return mapping.get(failure, failure)


def classify_groups(failures: list[str]) -> list[str]:
    groups: list[str] = []
    if "ai_rmf_800_218a_applied" in failures:
        groups.append("GROUP_AI")
    if any("13.8" in f or "8_reliability" in f for f in failures):
        groups.append("GROUP_GIPS")
    other = [
        f
        for f in failures
        if "ai_rmf" not in f and "13.8" not in f and "8_reliability" not in f
    ]
    if other:
        groups.append("GROUP_OTHER")
    return groups or ["GROUP_OTHER"]


def load_eng_ready_ids() -> list[int]:
    reg = load_register()
    return sorted(r["id"] for r in reg["rows"] if r["status"] == "ENGINEERING_READY" and r["id"] <= 826)


async def build_inventory(ids: list[int]) -> dict[str, Any]:
    reg = load_register()
    rows_by_id = {r["id"]: r for r in reg["rows"]}
    audits = await audit_ids(ids)
    runtime = await runtime_probe(ids)
    all_ai = set()
    for n in range(1, 18):
        all_ai |= set(discover_ai_cap_ids(n))

    entries: list[dict[str, Any]] = []
    group_ids: dict[str, list[int]] = {"GROUP_AI": [], "GROUP_GIPS": [], "GROUP_OTHER": []}

    for cid in ids:
        reg_row = rows_by_id[cid]
        aud = audits[cid]
        rt = runtime[cid]
        failures = aud.get("failure_columns", [])
        groups = classify_groups(failures)
        for g in groups:
            if cid not in group_ids[g]:
                group_ids[g].append(cid)
        ai_note = None
        ai_failed: list[str] = []
        if cid in all_ai:
            _, ai_note, ai_meta = phase3_ai_rmf_plus_218a(cid, rt if isinstance(rt, dict) else {})
            ai_failed = [x["id"] for x in (ai_meta or {}).get("218a_failed", [])]
        entries.append(
            {
                "id": cid,
                "capability": reg_row.get("capability"),
                "build_batch": reg_row.get("build_batch"),
                "official_batch": reg_row.get("official_batch"),
                "primary_hero": reg_row.get("primary_hero"),
                "groups": groups,
                "blocking_gates": [gate_label(f) for f in failures],
                "failure_columns": failures,
                "ai_218a_gaps": ai_failed,
                "ai_note": ai_note,
            }
        )

    return {
        "generated_at": _now(),
        "governing_standard": "institutional_due_diligence_2026/BLACKDARK_Institutional_Capability_Standard_2026_v6.md",
        "count": len(entries),
        "group_counts": {k: len(v) for k, v in group_ids.items()},
        "group_ids": group_ids,
        "entries": entries,
    }


def write_inventory_md(inv: dict[str, Any], path: Path) -> None:
    lines = [
        "# ENGINEERING_READY — 84 ID Inventory",
        "",
        f"**Generated:** {inv['generated_at']}",
        f"**Governing:** `{inv['governing_standard']}`",
        "",
        "## Summary",
        "",
        f"| Group | Count |",
        f"|-------|------:|",
    ]
    for g in ("GROUP_AI", "GROUP_GIPS", "GROUP_OTHER"):
        lines.append(f"| {g} | {inv['group_counts'][g]} |")
    lines.extend(
        [
            "",
            "IDs may appear in multiple groups when multiple gate families block closure.",
            "",
            "## GROUP_AI",
            "",
            "IDs: " + ", ".join(str(i) for i in inv["group_ids"]["GROUP_AI"]),
            "",
            "## GROUP_GIPS",
            "",
            "IDs: " + ", ".join(str(i) for i in inv["group_ids"]["GROUP_GIPS"]),
            "",
            "## GROUP_OTHER",
            "",
            "IDs: " + ", ".join(str(i) for i in inv["group_ids"]["GROUP_OTHER"]),
            "",
            "## Per-ID blocking gates",
            "",
            "| ID | Capability | Groups | Blocking gates |",
            "|---:|---|---|---|",
        ]
    )
    for e in inv["entries"]:
        gates = "; ".join(e["blocking_gates"][:3])
        if len(e["blocking_gates"]) > 3:
            gates += f" (+{len(e['blocking_gates']) - 3} more)"
        lines.append(
            f"| {e['id']} | {(e['capability'] or '')[:36]} | {','.join(e['groups'])} | {gates} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def reprocess_ids(ids: list[int], *, group_label: str) -> dict[str, Any]:
    from cap646.build826_heroes import enrich_binding_row, hero_binding_for

    reg = load_register()
    rows_by_id = {r["id"]: r for r in reg["rows"]}
    runtime = await runtime_probe(ids)
    audits = await audit_ids(ids)

    upgraded: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    failed = 0

    for cid in ids:
        row = rows_by_id[cid]
        aud = audits[cid]
        rt = runtime[cid]
        failures = aud.get("failure_columns", [])
        binding = hero_binding_for(cid)
        prior = row["status"]
        row.update(binding)
        enrich_binding_row(cid, row)

        if aud.get("fully_v6_compliant") and rt.get("success") and binding["hero_binding_status"] == "BOUND":
            row["status"] = "COMPLETE_V6"
            row["v6_fully_compliant"] = True
            row["blocker"] = None
            upgraded.append({"id": cid, "prior": prior, "evidence": aud.get("evidence_pack_12_met")})
        elif not rt.get("success"):
            row["status"] = "FAILED_GATE"
            row["v6_fully_compliant"] = False
            row["blocker"] = rt.get("error") or "runtime_fail"
            failed += 1
        elif binding["hero_binding_status"] == "UNBOUND":
            row["status"] = "PARTIAL"
            row["v6_fully_compliant"] = False
            row["blocker"] = ["hero_binding:UNBOUND", *failures[:4]]
        elif _core_gates_clean(failures):
            row["status"] = "ENGINEERING_READY"
            row["v6_fully_compliant"] = False
            row["blocker"] = failures[:6]
            remaining.append({"id": cid, "missing_gates": failures[:6]})
        else:
            row["status"] = "PARTIAL"
            row["v6_fully_compliant"] = False
            row["blocker"] = failures[:6]

        row["runtime_success"] = rt.get("success")
        row["updated_at"] = _now()

    reg["generated_at"] = _now()
    REGISTER_PATH.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_heroes_binding_index(reg)

    complete_total = sum(1 for r in reg["rows"] if r["status"] == "COMPLETE_V6")
    eng_total = sum(1 for r in reg["rows"] if r["status"] == "ENGINEERING_READY")
    partial_total = sum(1 for r in reg["rows"] if r["status"] == "PARTIAL")
    failed_total = sum(1 for r in reg["rows"] if r["status"] == "FAILED_GATE")

    log_line = (
        f"{_now()} ENG_READY_{group_label} | upgraded={len(upgraded)}/{len(ids)} | "
        f"complete_v6_total={complete_total}/826 | engineering_ready_total={eng_total} | "
        f"partial_total={partial_total} | failed={failed_total} | sha={_git_sha()}"
    )
    with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(log_line + "\n")

    report = BUILD_DIR / f"ENG_READY_{group_label}_REPORT.json"
    report.write_text(
        json.dumps(
            {
                "generated_at": _now(),
                "group": group_label,
                "processed": len(ids),
                "upgraded_complete_v6": [u["id"] for u in upgraded],
                "remaining_engineering_ready": remaining,
                "failed_gate": failed,
                "totals": {
                    "COMPLETE_V6": complete_total,
                    "ENGINEERING_READY": eng_total,
                    "PARTIAL": partial_total,
                    "FAILED_GATE": failed_total,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "log_line": log_line,
        "upgraded": upgraded,
        "remaining": remaining,
        "failed": failed,
        "totals": {
            "COMPLETE_V6": complete_total,
            "ENGINEERING_READY": eng_total,
            "PARTIAL": partial_total,
            "FAILED_GATE": failed_total,
        },
    }


def run_pytests(ids: list[int]) -> bool:
    batches = sorted({(cid - 1) // 25 + 1 for cid in ids})
    tests = [
        ROOT / f"tests/cap646/test_capability_build_batch{b:02d}.py"
        for b in batches
        if (ROOT / f"tests/cap646/test_capability_build_batch{b:02d}.py").is_file()
    ]
    if not tests:
        return True
    proc = subprocess.run(
        [PYTHON, "-m", "pytest", *[str(t.relative_to(ROOT)) for t in tests], "-q", "--tb=line"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    log = BUILD_DIR / "EVIDENCE" / "eng_ready_84_pytest.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return proc.returncode == 0


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--group", choices=["AI", "GIPS", "OTHER", "ALL"], default="ALL")
    args = ap.parse_args()

    ids = load_eng_ready_ids()
    if len(ids) != 84:
        print(f"WARN: expected 84 ENGINEERING_READY, found {len(ids)}")

    inv = await build_inventory(ids)
    write_inventory_md(inv, BUILD_DIR / "ENG_READY_84_INVENTORY.md")
    (BUILD_DIR / "ENG_READY_84_INVENTORY.json").write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")
    print(f"Inventory written — {inv['count']} IDs")

    if args.inventory_only:
        return 0

    if not run_pytests(ids):
        print("pytest failed — see EVIDENCE/eng_ready_84_pytest.log")
        return 1

    group_map = {
        "AI": inv["group_ids"]["GROUP_AI"],
        "GIPS": inv["group_ids"]["GROUP_GIPS"],
        "OTHER": inv["group_ids"]["GROUP_OTHER"],
    }

    results: dict[str, Any] = {}
    if args.group == "ALL":
        order = ["AI", "GIPS", "OTHER"]
    else:
        order = [args.group]

    for label in order:
        gids = group_map[label]
        if not gids:
            continue
        print(f"Processing {label}: {len(gids)} IDs …")
        results[label] = await reprocess_ids(gids, group_label=label)
        print(results[label]["log_line"])

    # Final closure report
    reg = load_register()
    final_inv = await build_inventory(
        sorted(r["id"] for r in reg["rows"] if r["status"] == "ENGINEERING_READY" and r["id"] <= 826)
    )
    complete = sum(1 for r in reg["rows"] if r["status"] == "COMPLETE_V6")
    eng = sum(1 for r in reg["rows"] if r["status"] == "ENGINEERING_READY")
    partial = sum(1 for r in reg["rows"] if r["status"] == "PARTIAL")
    failed = sum(1 for r in reg["rows"] if r["status"] == "FAILED_GATE")
    unbound = sum(
        1 for r in reg["rows"] if r.get("hero_binding_status") == "UNBOUND" and r["id"] <= 826
    )

    upgraded_all: list[int] = []
    for label in order:
        if label in results:
            upgraded_all.extend(u["id"] for u in results[label]["upgraded"])

    lines = [
        "# ENGINEERING_READY 84 — Closure Report",
        "",
        f"**Generated:** {_now()}",
        f"**Governing:** `{inv['governing_standard']}`",
        "",
        "## Inventory counts by group (initial)",
        "",
        f"| Group | Count |",
        f"|-------|------:|",
    ]
    for g in ("GROUP_AI", "GROUP_GIPS", "GROUP_OTHER"):
        lines.append(f"| {g} | {inv['group_counts'][g]} |")

    lines.extend(
        [
            "",
            "## Upgraded to COMPLETE_V6",
            "",
            f"Count: **{len(upgraded_all)}**",
            "",
            "IDs: " + (", ".join(str(i) for i in sorted(upgraded_all)) if upgraded_all else "—"),
            "",
            "Evidence: runtime v6 audit (`V6_LITERAL_COMPLIANCE_AUDIT_826.json`), "
            "`EVIDENCE/eng_ready_84_pytest.log`, per-group `ENG_READY_*_REPORT.json`.",
            "",
            "## Remaining ENGINEERING_READY",
            "",
            f"Count: **{eng}**",
            "",
        ]
    )
    for e in final_inv["entries"]:
        lines.append(f"- **{e['id']}** ({e['capability']}): {'; '.join(e['blocking_gates'][:2])}")

    lines.extend(
        [
            "",
            "## Final totals (honest — not 826/826 claim)",
            "",
            f"| Status | Count |",
            f"|--------|------:|",
            f"| COMPLETE_V6 | **{complete} / 826** |",
            f"| ENGINEERING_READY | {eng} / 826 |",
            f"| PARTIAL | {partial} |",
            f"| FAILED_GATE | {failed} |",
            f"| Hero UNBOUND | {unbound} |",
            "",
            "**Explicit:** Full spine COMPLETE_V6 is **not** claimed unless 826/826 is independently earned. "
            f"Current honest COMPLETE_V6 = **{complete}/826**.",
            "",
        ]
    )
    (BUILD_DIR / "ENG_READY_84_CLOSURE_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(
            f"{_now()} ENG_READY_84_CLOSURE | complete_v6={complete}/826 | engineering_ready={eng} | "
            f"partial={partial} | failed={failed} | unbound={unbound} | upgraded={len(upgraded_all)} | sha={_git_sha()}\n"
        )

    print(f"Final: COMPLETE_V6={complete} ENGINEERING_READY={eng} PARTIAL={partial} FAILED={failed}")
    return 0 if failed == 0 and unbound == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
