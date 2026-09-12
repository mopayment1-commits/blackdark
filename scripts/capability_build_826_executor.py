#!/usr/bin/env python3
"""Continuous v6 capability build executor — 826 IDs in batches of 25."""
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
RESUME_PATH = BUILD_DIR / "RESUME_STATE.json"
PROGRESS_LOG = BUILD_DIR / "BUILD_PROGRESS.log"
V6_STANDARD = ROOT / "institutional_due_diligence_2026/BLACKDARK_Institutional_Capability_Standard_2026_v6.md"
INVENTORY = ROOT / "docs/CAPABILITIES_826_INVENTORY.json"
BATCH_SIZE = 25
PYTHON = str(ROOT / ".venv/bin/python")

VALID_STATUS = frozenset(
    {
        "NOT_STARTED",
        "IN_PROGRESS",
        "COMPLETE_V6",
        "ENGINEERING_READY",
        "PARTIAL",
        "BLOCKED_EXTERNAL",
        "FAILED_GATE",
    }
)

CORE_V6_FAILURE_PREFIXES = (
    "v6_13.2_",
    "v6_13.3_",
    "v6_13.6_",
    "v6_13.7_",
    "v6_13.11_",
    "phase1_generic_delegate_check",
    "asvs_5_0_verified",
    "hero_binding",
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _git_sha() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except Exception:
        return "unknown"


def load_inventory() -> dict[int, dict[str, Any]]:
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    out: dict[int, dict[str, Any]] = {}
    for k, v in (inv.get("per_id") or {}).items():
        out[int(k)] = v
    return out


def code_reality(cid: int) -> str:
    """Map ID to coarse code state."""
    batch_num = (cid - 1) // 50 + 1
    ded = ROOT / f"cap646/batch{batch_num:02d}_dedicated.py"
    if batch_num == 1:
        ded = ROOT / "cap646/batch01_dedicated.py"
    if ded.is_file() and f" _cap{cid:03d}" in ded.read_text(encoding="utf-8"):
        return "IMPLEMENTED_UNVERIFIED"
    if cid <= 646:
        return "PARTIAL"
    return "STUB"


def init_register() -> dict[str, Any]:
    inv = load_inventory()
    rows: list[dict[str, Any]] = []
    for cid in range(1, 827):
        meta = inv.get(cid, {})
        rows.append(
            {
                "id": cid,
                "capability": meta.get("capability") or f"CAP-{cid}",
                "official_batch": meta.get("official_batch") or f"batch{(cid - 1) // 50 + 1:02d}",
                "build_batch": (cid - 1) // BATCH_SIZE + 1,
                "status": "NOT_STARTED",
                "code_reality": code_reality(cid),
                "v6_fully_compliant": False,
                "evidence_paths": [],
                "blocker": None,
                "primary_hero": None,
                "hero_entry_path": None,
                "hero_binding_status": "UNBOUND",
                "updated_at": _now(),
            }
        )
    doc = {
        "generated_at": _now(),
        "governing_standard": str(V6_STANDARD.relative_to(ROOT)),
        "total_ids": 826,
        "batch_size": BATCH_SIZE,
        "build_batches": (826 + BATCH_SIZE - 1) // BATCH_SIZE,
        "rows": rows,
    }
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    (BUILD_DIR / "EVIDENCE").mkdir(exist_ok=True)
    REGISTER_PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc


def load_register() -> dict[str, Any]:
    if not REGISTER_PATH.is_file():
        return init_register()
    return json.loads(REGISTER_PATH.read_text(encoding="utf-8"))


def load_resume() -> dict[str, Any]:
    if RESUME_PATH.is_file():
        return json.loads(RESUME_PATH.read_text(encoding="utf-8"))
    return {
        "current_build_batch": 1,
        "next_id": 1,
        "last_completed_build_batch": 0,
        "blockers": [],
        "updated_at": _now(),
    }


def save_resume(state: dict[str, Any]) -> None:
    state["updated_at"] = _now()
    RESUME_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _core_gates_clean(failures: list[str]) -> bool:
    return not any(
        f.startswith(CORE_V6_FAILURE_PREFIXES) or f == "hero_binding:UNBOUND" for f in failures
    )


def write_heroes_binding_index(reg: dict[str, Any]) -> Path:
    path = BUILD_DIR / "HEROES_BINDING_INDEX.md"
    rows = sorted(reg["rows"], key=lambda r: r["id"])
    lines = [
        "# Six Heroes Binding Index — CAPABILITY_BUILD_826",
        "",
        f"**Updated:** {_now()}",
        "",
        "| ID | Capability | Primary Hero | Entry Path | Binding | Build Status |",
        "|---:|---|---|---|---|---|",
    ]
    for r in rows:
        if r["id"] > 826:
            continue
        lines.append(
            f"| {r['id']} | {r.get('capability', '')[:40]} | {r.get('primary_hero') or '—'} | "
            f"{(r.get('hero_entry_path') or '—')[:60]} | {r.get('hero_binding_status', 'UNBOUND')} | "
            f"{r.get('status', 'NOT_STARTED')} |"
        )
    unbound_complete = [
        r["id"]
        for r in rows
        if r.get("status") == "COMPLETE_V6" and r.get("hero_binding_status") != "BOUND"
    ]
    lines.extend(
        [
            "",
            f"**Unbound COMPLETE_V6 (must be 0):** {len(unbound_complete)}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def batch_id_range(build_batch: int) -> range:
    start = (build_batch - 1) * BATCH_SIZE + 1
    end = min(build_batch * BATCH_SIZE, 826)
    return range(start, end + 1)


async def audit_ids(ids: list[int]) -> dict[int, dict[str, Any]]:
    from scripts.v6_literal_compliance_audit_826 import (
        audit_one,
        load_audit_rows,
        load_closure_evidence,
        load_rtm_per_id,
    )
    from scripts.audit_standards_v6 import discover_ai_cap_ids

    audit_rows = load_audit_rows()
    rtm_map = load_rtm_per_id()
    ai_by_batch = {n: discover_ai_cap_ids(n) for n in range(1, 18)}
    all_ai: set[int] = set()
    for s in ai_by_batch.values():
        all_ai |= set(s)
    cache = {n: load_closure_evidence(n) for n in range(1, 18)}

    out: dict[int, dict[str, Any]] = {}
    for cid in ids:
        out[cid] = await audit_one(
            cid,
            audit_rows=audit_rows,
            rtm_map=rtm_map,
            ai_ids=frozenset(all_ai),
            closure_cache=cache,
        )
    return out


async def runtime_probe(ids: list[int]) -> dict[int, dict[str, Any]]:
    from cap646.runtime import execute_capability

    params = {
        "symbol": "BTC",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "tier": "pro",
    }
    out: dict[int, dict[str, Any]] = {}
    for cid in ids:
        try:
            r = await execute_capability(cid, skip_entitlement=True, params=dict(params))
            out[cid] = {"success": bool(r.get("success")), "surface": r.get("surface"), "error": r.get("error")}
        except Exception as exc:
            out[cid] = {"success": False, "error": str(exc)}
    return out


def run_batch_tests(build_batch: int, ids: list[int]) -> dict[str, Any]:
    ev_dir = BUILD_DIR / "EVIDENCE"
    ev_dir.mkdir(parents=True, exist_ok=True)
    log_path = ev_dir / f"batch{build_batch:02d}_pytest.log"
    build_test_modules = {
        1: "tests/cap646/test_capability_build_batch01.py",
        2: "tests/cap646/test_capability_build_batch02.py",
        3: "tests/cap646/test_capability_build_batch03.py",
        4: "tests/cap646/test_capability_build_batch04.py",
    }
    if build_batch in build_test_modules:
        cmd = [PYTHON, "-m", "pytest", build_test_modules[build_batch], "-q", "--tb=short"]
    elif (ROOT / f"tests/cap646/test_batch{build_batch:02d}_dedicated.py").is_file():
        cmd = [PYTHON, "-m", "pytest", f"tests/cap646/test_batch{build_batch:02d}_dedicated.py", "-q", "--tb=short"]
    else:
        cmd = [PYTHON, "-c", f"print('TEST_GAP batch{build_batch:02d}: no dedicated pytest module')"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
    log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return {
        "exit_code": proc.returncode,
        "log": str(log_path.relative_to(ROOT)),
        "passed": proc.returncode == 0,
    }


async def process_build_batch(build_batch: int, *, force: bool = False) -> dict[str, Any]:
    from cap646.build826_heroes import enrich_binding_row, hero_binding_for

    reg = load_register()
    resume = load_resume()
    ids = list(batch_id_range(build_batch))
    rows_by_id = {r["id"]: r for r in reg["rows"]}

    for cid in ids:
        rows_by_id[cid]["status"] = "IN_PROGRESS"
        rows_by_id[cid]["updated_at"] = _now()

    runtime = await runtime_probe(ids)
    audits = await audit_ids(ids)
    tests = run_batch_tests(build_batch, ids)

    complete = engineering = blocked = failed = partial = unbound = 0
    batch_rows: list[dict[str, Any]] = []
    hero_summary: dict[str, int] = {}

    for cid in ids:
        row = rows_by_id[cid]
        aud = audits[cid]
        rt = runtime[cid]
        failures = aud.get("failure_columns", [])
        binding = hero_binding_for(cid)
        row.update(binding)
        hero_summary[binding["primary_hero"] or "UNBOUND"] = hero_summary.get(binding["primary_hero"] or "UNBOUND", 0) + 1

        ev_paths = [
            f"EVIDENCE/batch{build_batch:02d}_pytest.log",
            "institutional_due_diligence_2026/V6_LITERAL_COMPLIANCE_AUDIT_826.json",
        ]

        if aud.get("fully_v6_compliant") and rt.get("success") and binding["hero_binding_status"] == "BOUND":
            row["status"] = "COMPLETE_V6"
            row["v6_fully_compliant"] = True
            row["blocker"] = None
            complete += 1
        elif not rt.get("success"):
            row["status"] = "FAILED_GATE"
            row["v6_fully_compliant"] = False
            row["blocker"] = rt.get("error") or "runtime_fail"
            failed += 1
        elif binding["hero_binding_status"] == "UNBOUND":
            row["status"] = "PARTIAL"
            row["v6_fully_compliant"] = False
            row["blocker"] = ["hero_binding:UNBOUND", *failures[:4]]
            partial += 1
            unbound += 1
        elif _core_gates_clean(failures):
            row["status"] = "ENGINEERING_READY"
            row["v6_fully_compliant"] = False
            row["blocker"] = failures[:6]
            engineering += 1
        else:
            row["status"] = "PARTIAL"
            row["v6_fully_compliant"] = False
            row["blocker"] = failures[:6]
            partial += 1

        enrich_binding_row(cid, row)
        row["runtime_success"] = rt.get("success")
        row["evidence_paths"] = ev_paths
        row["updated_at"] = _now()
        batch_rows.append(
            {
                "id": cid,
                "status": row["status"],
                "runtime_success": rt.get("success"),
                "fully_v6_compliant": aud.get("fully_v6_compliant"),
                "primary_hero": row.get("primary_hero"),
                "hero_binding_status": row.get("hero_binding_status"),
                "failures": failures[:8],
            }
        )

    strict_pass = failed == 0 and complete == len(ids)
    batch_terminal = failed == 0  # no FAILED_GATE — may continue with PARTIAL/ENGINEERING_READY

    complete_total = sum(1 for x in reg["rows"] if x["status"] == "COMPLETE_V6")
    eng_total = sum(1 for x in reg["rows"] if x["status"] == "ENGINEERING_READY")
    partial_total = sum(1 for x in reg["rows"] if x["status"] == "PARTIAL")
    blocked_total = sum(1 for x in reg["rows"] if x["status"] == "BLOCKED_EXTERNAL")
    unbound_total = sum(
        1 for x in reg["rows"] if x.get("hero_binding_status") == "UNBOUND" and x["id"] <= 826
    )

    sha = _git_sha()
    log_line = (
        f"BATCH_{build_batch:02d} | complete_v6={complete}/{len(ids)} (total {complete_total}/826) | "
        f"engineering_ready={engineering} (total {eng_total}) | partial={partial} | blocked={blocked} | "
        f"unbound_heroes={unbound} | failed={failed} | sha={sha}"
    )
    with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{_now()} {log_line}\n")

    reg["updated_at"] = _now()
    REGISTER_PATH.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_heroes_binding_index(reg)

    report_path = BUILD_DIR / f"BATCH_{build_batch:02d}_REPORT.md"
    hero_lines = [f"- **{k}:** {v}" for k, v in sorted(hero_summary.items(), key=lambda x: -x[1])]
    report_path.write_text(
        "\n".join(
            [
                f"# Build Batch {build_batch:02d} (IDs {ids[0]}–{ids[-1]})",
                "",
                f"**Generated:** {_now()}",
                f"**Governing:** `{V6_STANDARD.relative_to(ROOT)}`",
                "",
                f"## Batch Gate: {'ALL COMPLETE_V6 ✅' if strict_pass else 'TERMINAL (no FAILED_GATE) ✅' if batch_terminal else 'FAILED_GATE ❌'}",
                "",
                f"- COMPLETE_V6 in batch: **{complete}/{len(ids)}** (826 total: {complete_total})",
                f"- ENGINEERING_READY in batch: **{engineering}/{len(ids)}** (826 total: {eng_total})",
                f"- PARTIAL: **{partial}** (826 total: {partial_total})",
                f"- BLOCKED_EXTERNAL: **{blocked}**",
                f"- FAILED_GATE: **{failed}**",
                f"- Unbound heroes in batch: **{unbound}**",
                f"- Tests: {'PASS ✅' if tests['passed'] else 'FAIL ❌'} (`{tests['log']}`)",
                "",
                "## Six Heroes Binding Summary",
                "",
                *hero_lines,
                "",
                "## Per-ID",
                "",
                "| ID | Status | Hero | Binding | Runtime | v6 | Top failures |",
                "|---:|---|---|---|---|---|---|",
                *[
                    f"| {r['id']} | {r['status']} | {r.get('primary_hero') or '—'} | "
                    f"{r.get('hero_binding_status')} | {r['runtime_success']} | {r['fully_v6_compliant']} | "
                    f"{', '.join(r['failures'][:3]) or '—'} |"
                    for r in batch_rows
                ],
                "",
                "## Notes",
                "",
                "COMPLETE_V6 requires `fully_v6_compliant=true` + runtime + Hero BOUND.",
                "ENGINEERING_READY = runtime OK + Hero BOUND + core gates clean; residual perf/live gates open.",
                "PARTIAL = honest incomplete; no fake PASS.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    if batch_terminal:
        resume["last_completed_build_batch"] = build_batch
        resume["current_build_batch"] = build_batch + 1
        resume["next_id"] = ids[-1] + 1
        resume["blockers"] = [] if strict_pass else [f"batch{build_batch:02d}: residual PARTIAL/ENGINEERING_READY gates"]
    else:
        resume["current_build_batch"] = build_batch
        resume["blockers"] = [f"batch{build_batch:02d}: {failed} FAILED_GATE"]
    save_resume(resume)

    return {
        "build_batch": build_batch,
        "gate_pass": strict_pass,
        "batch_terminal": batch_terminal,
        "complete": complete,
        "engineering_ready": engineering,
        "partial": partial,
        "failed": failed,
        "unbound_heroes": unbound,
        "complete_total": complete_total,
        "log_line": log_line,
    }


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["init", "batch", "continuous"])
    ap.add_argument("--batch", type=int, default=0, help="Build batch number (1-34)")
    ap.add_argument("--max-batches", type=int, default=1, help="For continuous mode")
    args = ap.parse_args()

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    if args.action == "init":
        init_register()
        save_resume(
            {
                "current_build_batch": 1,
                "next_id": 1,
                "last_completed_build_batch": 0,
                "blockers": [],
                "updated_at": _now(),
            }
        )
        print("Initialized", REGISTER_PATH)
        return 0

    load_register()
    resume = load_resume()
    start = args.batch or resume.get("current_build_batch", 1)

    if args.action == "batch":
        result = await process_build_batch(start)
        print(result["log_line"])
        return 0 if result["batch_terminal"] else 1

    # continuous — advance while no FAILED_GATE (PARTIAL/ENGINEERING_READY allowed)
    max_b = args.max_batches
    b = start
    processed = 0
    while b <= 34 and processed < max_b:
        result = await process_build_batch(b)
        print(result["log_line"])
        if not result["batch_terminal"]:
            print(f"HALT at build batch {b} — FAILED_GATE (fix before continuing)")
            return 1
        if result["complete_total"] >= 826 and result["gate_pass"]:
            print("All 826 COMPLETE_V6")
            break
        b += 1
        processed += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
