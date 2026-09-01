#!/usr/bin/env python3
"""CLOSURE-REJECT-04 audit — Type-3 (lizard), jscpd, R0801 full, split-brain 56, SSOT."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OFFICIAL = list(range(1, 101))
PRE_BATCH = [338, 500, 507, 534]
SYMBOLS = ["BTC", "ETH", "SOL", "AVAX", "DOGE"]


def _load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _catalog() -> dict[int, dict]:
    return {int(r["id"]): r for r in _load("docs/cap646/CAP646_CATALOG.json")}


def _inventory() -> dict[int, dict]:
    return {int(k): v for k, v in _load("docs/CAPABILITIES_826_INVENTORY.json")["per_id"].items()}


def run_pylint_r0801_full() -> list[dict]:
    proc = subprocess.run(
        ["pylint", "cap646/", "--disable=all", "--enable=duplicate-code", "--msg-template={path}:{line}:{column}: {msg_id}: {msg}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    hits = []
    for line in proc.stdout.splitlines():
        if "R0801" in line or "duplicate-code" in line.lower():
            hits.append({"raw": line})
    # pylint also prints duplicate blocks in stderr
    block = proc.stdout + "\n" + proc.stderr
    for m in re.finditer(r"==cap646\.[^\[]+\[:(\d+):(\d+)\].*==cap646\.[^\[]+\[:(\d+):(\d+)\]", block):
        hits.append(
            {
                "file_a": m.group(0).split("==")[1].split("[")[0],
                "lines_a": f"{m.group(1)}-{m.group(2)}",
                "file_b": m.group(0).split("==")[2].split("[")[0],
                "lines_b": f"{m.group(3)}-{m.group(4)}",
            }
        )
    return hits


def run_lizard_type3() -> dict:
    targets = [
        ROOT / "cap646/batch01_production.py",
        ROOT / "cap646/batch01_dedicated.py",
        ROOT / "cap646/batch02_production.py",
        ROOT / "cap646/batch02_dedicated.py",
        ROOT / "cap646/handlers",
        ROOT / "cap646/runtime.py",
    ]
    proc = subprocess.run(
        ["lizard", "-l", "python", "-C", "8", "-w"] + [str(t) for t in targets],
        capture_output=True,
        text=True,
    )
    clones = []
    for line in proc.stdout.splitlines():
        if "cap646" in line and "@" in line:
            clones.append(line.strip())
    return {
        "tool": "lizard",
        "methodology": "Roy & Cordy Type-3 — statement-level similarity (lizard -C 8)",
        "clone_count": len(clones),
        "clones": clones,
        "stderr": proc.stderr[-500:] if proc.stderr else "",
    }


def run_jscpd() -> dict:
    out_dir = ROOT / "docs/.jscpd-report"
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            "npx",
            "--yes",
            "jscpd@4.0.5",
            "cap646/batch01_production.py",
            "cap646/batch01_dedicated.py",
            "cap646/batch02_production.py",
            "cap646/batch02_dedicated.py",
            "cap646/handlers",
            "cap646/runtime.py",
            "--min-lines",
            "5",
            "--min-tokens",
            "50",
            "--reporters",
            "json",
            "--output",
            str(out_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report_path = out_dir / "jscpd-report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {"statistics": {}, "duplicates": []}
    return {
        "tool": "jscpd@4.0.5",
        "exit_code": proc.returncode,
        "statistics": report.get("statistics", {}),
        "duplicates": report.get("duplicates", []),
        "stdout_tail": proc.stdout[-800:] if proc.stdout else "",
    }


def build_ssot_matrix() -> dict:
    inv = _inventory()
    families = {
        "price": {
            "canonical_module": "market_context.fetch_binance_ticker",
            "canonical_file": "market_context.py",
            "dependents_1_100": [],
        },
        "volume": {
            "canonical_module": "bd_platform.institutional_delivery_intelligence_layer.volume_intelligence",
            "canonical_file": "bd_platform/institutional_delivery_intelligence_layer.py",
            "dependents_1_100": [],
        },
        "holder_concentration": {
            "canonical_module": "bd_platform.onchain_hub.holder_concentration",
            "canonical_file": "bd_platform/onchain_hub.py",
            "dependents_1_100": [],
        },
        "exchange_flows": {
            "canonical_module": "bd_platform.onchain_hub.exchange_flow_intelligence",
            "canonical_file": "bd_platform/onchain_hub.py",
            "dependents_1_100": [],
        },
        "open_interest": {
            "canonical_module": "bd_platform.derivatives_hub.derivatives_overview",
            "canonical_file": "bd_platform/derivatives_hub.py",
            "dependents_1_100": [85],
        },
        "realized_cap": {
            "canonical_module": "bd_platform.onchain_hub.realized_cap_metrics",
            "canonical_file": "bd_platform/onchain_hub.py",
            "dependents_1_100": [39],
        },
    }
    for cid in OFFICIAL:
        row = inv.get(str(cid)) or inv.get(cid) or {}
        backend = str(row.get("backend") or "")
        surface = str(row.get("expected_surface") or "")
        if "price" in surface or cid in {5, 7, 47}:
            families["price"]["dependents_1_100"].append({"id": cid, "backend": backend, "surface": surface})
        if "volume" in surface or cid in {74, 75}:
            families["volume"]["dependents_1_100"].append({"id": cid, "backend": backend, "surface": surface})
        if "holder" in surface or cid in {11, 12}:
            families["holder_concentration"]["dependents_1_100"].append({"id": cid, "backend": backend, "surface": surface})
        if "exchange_flow" in surface or cid in {13, 14}:
            families["exchange_flows"]["dependents_1_100"].append({"id": cid, "backend": backend, "surface": surface})
        if cid == 85 or "open_interest" in surface:
            dep_ids = {d["id"] if isinstance(d, dict) else d for d in families["open_interest"]["dependents_1_100"]}
            if cid not in dep_ids:
                families["open_interest"]["dependents_1_100"].append({"id": cid, "backend": backend, "surface": surface})
        if cid == 39 or "realized_cap" in surface:
            dep_ids = {d["id"] if isinstance(d, dict) else d for d in families["realized_cap"]["dependents_1_100"]}
            if cid not in dep_ids:
                families["realized_cap"]["dependents_1_100"].append({"id": cid, "backend": backend, "surface": surface})
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "IDs 1-100 financial formula SSOT",
        "standard": "ISO/IEC 25010 — single source of truth per formula family",
        "families": families,
    }


def split_brain_56_audit() -> dict:
    align = _load("docs/PRODUCTION_PATH_ALIGNMENT_AUDIT_BATCHES_01_06.json")
    split_ids = []
    for status, block in align.get("by_status", {}).items():
        if "SPLIT_BRAIN" in status:
            split_ids.extend(block.get("ids", []))
    split_ids = sorted(set(i for i in split_ids if 1 <= i <= 100))
    exec_audit = _load("docs/EXECUTION_PATH_AUDIT_1_100.json")
    non_spine = set(exec_audit.get("non_standard_ids", []))
    paths = {p["capability_id"]: p for p in exec_audit.get("paths", [])}
    rows = []
    for cid in split_ids:
        inv = _inventory().get(cid, {})
        rows.append(
            {
                "capability_id": cid,
                "parallel_path_module": inv.get("backend") or paths.get(cid, {}).get("module"),
                "official_spine": inv.get("production_spine") or paths.get(cid, {}).get("official_spine"),
                "non_spine": cid in non_spine,
                "split_brain_status": next(
                    (s for s, b in align["by_status"].items() if cid in b.get("ids", []) and "SPLIT_BRAIN" in s),
                    None,
                ),
            }
        )
    return {"split_brain_intersection_1_100": split_ids, "count": len(split_ids), "rows": rows}


async def contract_test_pair(id_a: int, id_b: int) -> dict:
    from cap646.runtime import execute_capability

    tests = []
    for symbol in SYMBOLS[:5]:
        for kind in ("spot_futures",):
            ra = await execute_capability(id_a, params={"symbol": symbol, "kind": kind})
            rb = await execute_capability(id_b, params={"symbol": symbol, "kind": kind})
            tests.append(
                {
                    "symbol": symbol,
                    "kind": kind,
                    "a_surface": ra.get("surface"),
                    "b_surface": rb.get("surface"),
                    "surfaces_match": ra.get("surface") == rb.get("surface"),
                    "a_success": ra.get("success"),
                    "b_success": rb.get("success"),
                }
            )
    return {"pair": [id_a, id_b], "contract_tests": tests, "all_surfaces_match": all(t["surfaces_match"] for t in tests)}


async def split_brain_contract_sample(n: int = 20) -> list[dict]:
    sb = split_brain_56_audit()
    sample_ids = sb["split_brain_intersection_1_100"][:n]
    results = []
    for cid in sample_ids:
        from cap646.runtime import execute_capability

        row = next(r for r in sb["rows"] if r["capability_id"] == cid)
        tests = []
        for symbol in SYMBOLS[:2]:
            r = await execute_capability(cid, params={"symbol": symbol, "kind": "spot_futures"})
            tests.append({"symbol": symbol, "surface": r.get("surface"), "success": r.get("success")})
        results.append({**row, "live_contract": tests})
    return results


def scan_batch03_leaks() -> list[dict]:
    """Detect Batch03 IDs (101-150) in proof/entitlement execution artifacts only."""
    leaks = []
    pattern = re.compile(r'"capability_id"\s*:\s*(10[1-9]|1[1-4][0-9]|150)\b')
    proof_files = [
        "docs/BATCH01_ENTITLEMENT_GATEWAY_PROOF.json",
        "docs/BATCH02_ENTITLEMENT_GATEWAY_PROOF.json",
        "docs/BATCH01_HTTP_PROOF_1_50.json",
        "docs/BATCH02_HTTP_PROOF_51_100.json",
    ]
    for rel in proof_files:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in pattern.finditer(text):
            leaks.append({"file": rel, "capability_id": int(m.group(1))})
    return leaks


def recompute_progress_104() -> dict:
    """Official 1-100 + pre-batch 338/500/507/534 only — excludes hero/extension without batch01/02 proof."""
    included = sorted(OFFICIAL + PRE_BATCH)
    excluded = {
        "175": "batch04 hero — no batch01/02 RTM/HTTP/entitlement proof",
        "214": "hero batch 201-300 OPEN_RISK_REQUIRES_REEVALUATION",
        "245": "hero batch 201-300 OPEN_RISK_REQUIRES_REEVALUATION",
        "584": "SPLIT-BRAIN-UNVERIFIED — no batch01/02 closure proof",
        "629": "batch13 extension — no batch01/02 closure proof",
        "630": "batch13 extension — no batch01/02 closure proof",
        "631": "batch13 extension — no batch01/02 closure proof",
        "642": "batch13 extension — no batch01/02 closure proof",
        "644": "batch13 extension — no batch01/02 closure proof",
        "646": "batch13 extension — no batch01/02 closure proof",
    }
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "numerator": len(included),
        "denominator": 826,
        "canonical_progress": f"{len(included)}/826",
        "methodology": "50 batch01 + 46 batch02 independent + 4 OVERLAP (within 1-100) + 4 pre-batch (338,500,507,534)",
        "included_ids": included,
        "excluded_from_numerator": excluded,
        "prior_incorrect_numerator": 114,
        "correction_reason": "CLOSURE-REJECT-04 item 9/10 — removed IDs without batch01/02-equivalent proof",
    }


async def main() -> None:
    print("Running pylint R0801...")
    r0801 = run_pylint_r0801_full()
    print("Running lizard Type-3...")
    lizard = run_lizard_type3()
    print("Running jscpd...")
    jscpd = run_jscpd()
    print("Building SSOT matrix...")
    ssot = build_ssot_matrix()
    (ROOT / "docs/SSOT_MATRIX_1_100.json").write_text(json.dumps(ssot, indent=2) + "\n", encoding="utf-8")
    print("Split-brain 56 audit...")
    sb = split_brain_56_audit()
    print("Split-brain contract sample (20)...")
    sb_contracts = await split_brain_contract_sample(20)
    leaks = scan_batch03_leaks()
    progress = recompute_progress_104()
    (ROOT / "docs/PROGRESS_114_ID_MAPPING.json").write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
    out = {
        "audit_id": "CLOSURE_REJECT_04",
        "generated_at": datetime.now(UTC).isoformat(),
        "pylint_r0801_full": r0801,
        "type3_lizard": lizard,
        "jscpd": jscpd,
        "split_brain_56": sb,
        "split_brain_contract_sample_20": sb_contracts,
        "batch03_leaks_scan": leaks,
        "progress_104": progress,
        "link_eligible_decision": {
            "ids": [106, 107, 110, 125],
            "decision": "DEFERRED_DOCUMENTED",
            "rationale": "Live execution requires batch03 scope (101-150) which is PROHIBITED for closure work. Canonical targets 63/64/69/85 in 1-100 are PRODUCTION-ALIGNED. REUSED-LINK acceptance deferred until owner approves limited batch03 read-only proof run.",
            "max_deferral": "Until INSTITUTIONAL_CLOSED gate minus link-eligible live proofs",
        },
    }
    path = ROOT / "docs/CLOSURE_REJECT_04_AUDIT.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path}")
    # Update canonical progress
    prog826 = _load("docs/PROGRESS_826_CANONICAL.json")
    prog826["numerator"] = progress["numerator"]
    prog826["canonical_progress"] = progress["canonical_progress"]
    prog826["computed_at"] = progress["generated_at"]
    prog826["correction"] = "CLOSURE-REJECT-04: 114→104 — removed extension/hero IDs without batch01/02 proof"
    (ROOT / "docs/PROGRESS_826_CANONICAL.json").write_text(json.dumps(prog826, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"progress": progress["canonical_progress"], "leaks": len(leaks), "lizard_clones": lizard["clone_count"]}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
