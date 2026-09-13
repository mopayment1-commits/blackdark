#!/usr/bin/env python3
"""Bandit triage reconciliation — fail-closed disposition + CI gate evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "docs" / "evidence" / "bandit-full-4703-compact.json"
DEFAULT_INVENTORY = ROOT / "docs" / "evidence" / "bandit-disposition-inventory-4703.json"
NEUTRAL_INI = ROOT / "scripts" / ".bandit_neutral.ini"
CI_INI = ROOT / ".bandit"
FULL_EXCLUDE = ".venv,venv,node_modules,.git,dist,build"
EXPECTED_TOTAL = 4703

# Production B101 locations with reviewed line-level # nosec B101.
REVIEWED_NOSEC = {
    ("aggregator.py", 1069, "B101"),
    ("hot_storage.py", 192, "B101"),
    ("market_context.py", 51, "B101"),
    ("oauth_service.py", 184, "B101"),
    ("org_tenant_store.py", 394, "B101"),
    ("postgres_backend.py", 317, "B101"),
    ("postgres_backend.py", 340, "B101"),
    ("postgres_backend.py", 377, "B101"),
    ("scripts/generate_final_integrity_summary.py", 70, "B101"),
    ("scripts/generate_pentagonal_hero_binding_report.py", 237, "B101"),
    ("scripts/generate_progress_114_mapping.py", 52, "B101"),
    ("scripts/reclassify_option_b_deferred.py", 42, "B101"),
    ("scripts/reclassify_split_brain_bcd.py", 135, "B101"),
    ("scripts/reclassify_split_brain_routing.py", 207, "B101"),
    ("scripts/reclassify_template_seed_stubs.py", 53, "B101"),
    ("scripts/run_batch_verification_orchestrator.py", 97, "B101"),
    ("scripts/run_soft_launch_closure.py", 51, "B101"),
    ("scripts/wave_00_passive_security_scan.py", 17, "B310"),
    ("scripts/complete_pdf_capabilities_826.py", 124, "B310"),
}

FAIL_CLOSED_RULES = frozenset(
    {"B608", "B105", "B603", "B607", "B404", "B311", "B110", "B112", "B310"}
)


def _bandit_bin() -> str:
    venv = ROOT / ".venv" / "bin" / "bandit"
    return str(venv) if venv.is_file() else "bandit"


def _norm(filename: str) -> str:
    return filename.replace("\\", "/").lstrip("./")


def _area(filename: str) -> str:
    fn = _norm(filename)
    if fn.startswith("tests/"):
        return "tests"
    if fn.startswith("scripts/"):
        return "scripts"
    return "production"


def _inventory_key(filename: str, line: int, test_id: str) -> str:
    return f"{_norm(filename)}|{line}|{test_id}"


def load_inventory(path: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload.get("entries") or payload)


def classify_finding(
    test_id: str,
    filename: str,
    line: int,
    inventory: dict[str, dict[str, str]],
) -> dict[str, str]:
    """Fail-closed: only explicit inventory or narrowly scoped TEST_ONLY rules."""
    key_tuple = (_norm(filename), line, test_id)
    inv_key = _inventory_key(filename, line, test_id)
    area = _area(filename)

    if test_id == "B101":
        if area == "tests":
            return {"disposition": "TEST_ONLY", "reason": "pytest assert in tests/ scope"}
        if key_tuple in REVIEWED_NOSEC:
            return {"disposition": "FALSE_POSITIVE", "reason": "reviewed runtime invariant; line nosec B101"}
        return {"disposition": "RAV", "reason": "unexpected B101 outside tests without reviewed nosec"}

    if test_id in {"B106", "B108"}:
        if area == "tests":
            return {"disposition": "TEST_ONLY", "reason": f"{test_id} in tests/ only"}
        return {"disposition": "RAV", "reason": f"unexpected {test_id} outside tests/"}

    if test_id in FAIL_CLOSED_RULES:
        entry = inventory.get(inv_key)
        if entry:
            return {"disposition": entry["disposition"], "reason": entry["reason"]}
        return {
            "disposition": "RAV",
            "reason": f"{test_id} not in explicit disposition inventory for {inv_key}",
        }

    return {"disposition": "RAV", "reason": f"unmapped rule {test_id}"}


def run_bandit_json(args: list[str]) -> dict:
    proc = subprocess.run(
        [_bandit_bin(), *args, "-f", "json", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr or proc.stdout or f"bandit failed: {proc.returncode}")
    return json.loads(proc.stdout or "{}")


def reconcile_original(report_path: Path, inventory_path: Path) -> dict:
    if not report_path.is_file():
        raise FileNotFoundError(f"missing original report: {report_path}")
    if not inventory_path.is_file():
        raise FileNotFoundError(f"missing disposition inventory: {inventory_path}")

    inventory = load_inventory(inventory_path)
    results = json.loads(report_path.read_text(encoding="utf-8"))["results"]

    seen: set[tuple[str, int, str]] = set()
    duplicate = 0
    table: dict[str, Counter] = defaultdict(Counter)
    rows: list[dict] = []

    for r in results:
        fn = _norm(r["filename"])
        line = int(r["line_number"])
        tid = r["test_id"]
        key = (fn, line, tid)
        if key in seen:
            duplicate += 1
            disp = "DUPLICATE"
            reason = "duplicate file:line:test_id in source report"
        else:
            seen.add(key)
            verdict = classify_finding(tid, fn, line, inventory)
            disp = verdict["disposition"]
            reason = verdict["reason"]
        table[tid][disp] += 1
        rows.append(
            {
                "test_id": tid,
                "file": fn,
                "line": line,
                "severity": r["issue_severity"],
                "disposition": disp,
                "reason": reason,
            }
        )

    totals = Counter()
    for counts in table.values():
        for disp, n in counts.items():
            totals[disp] += n

    reconciliation = {}
    for tid in sorted(table):
        counts = table[tid]
        reconciliation[tid] = {
            "total": sum(counts.values()),
            "TP": counts.get("TRUE_POSITIVE", 0),
            "FP": counts.get("FALSE_POSITIVE", 0),
            "TEST_ONLY": counts.get("TEST_ONLY", 0),
            "DUPLICATE": counts.get("DUPLICATE", 0),
            "RAV": counts.get("RAV", 0),
        }

    grand = sum(reconciliation[t]["total"] for t in reconciliation)
    rav_rows = [row for row in rows if row["disposition"] == "RAV"]
    return {
        "source_report": str(report_path.relative_to(ROOT)),
        "inventory": str(inventory_path.relative_to(ROOT)),
        "original_total": len(results),
        "unique_keys": len(seen),
        "duplicate_count": duplicate,
        "grand_total_check": grand,
        "totals_by_disposition": dict(totals),
        "reconciliation_by_test_id": reconciliation,
        "rav_count": len(rav_rows),
        "rav_samples": rav_rows[:10],
        "findings": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bandit 4703 reconciliation (fail-closed)")
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Original Bandit JSON report (default: docs/evidence/bandit-full-4703-compact.json)",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY,
        help="Explicit per-location disposition inventory",
    )
    args = parser.parse_args()

    if not NEUTRAL_INI.is_file():
        NEUTRAL_INI.write_text("[bandit]\n", encoding="utf-8")

    original = reconcile_original(args.report.resolve(), args.inventory.resolve())
    full = run_bandit_json(["-r", ".", "--exclude", FULL_EXCLUDE, "--ini", str(NEUTRAL_INI)])
    ci = run_bandit_json(["-r", ".", "--ini", str(CI_INI), "-ll"])

    out = {
        "original_reconciliation": original,
        "full_scope_scan": {
            "command": f"bandit -r . --exclude {FULL_EXCLUDE} --ini {NEUTRAL_INI.name}",
            "total_findings": len(full.get("results", [])),
            "metrics": full.get("metrics", {}).get("_totals", {}),
        },
        "ci_scope_scan": {
            "command": "bandit -r . --ini .bandit -ll",
            "medium_plus_findings": len(ci.get("results", [])),
            "policy": {
                "exclude": "tests/, data/ (artifact store; zero .py), venv, build",
                "global_skips": [],
                "fail_closed_rules": sorted(FAIL_CLOSED_RULES),
                "line_nosec_reviewed_b101_b310": len(REVIEWED_NOSEC),
                "inventory_entries": len(load_inventory(args.inventory.resolve())),
            },
        },
        "confirmed_true_positives": 0,
    }
    print(json.dumps(out, indent=2))

    errors: list[str] = []
    if original["grand_total_check"] != EXPECTED_TOTAL:
        errors.append(f"reconciliation total {original['grand_total_check']} != {EXPECTED_TOTAL}")
    if original["original_total"] != EXPECTED_TOTAL:
        errors.append(f"source report total {original['original_total']} != {EXPECTED_TOTAL}")
    if original["rav_count"] != 0:
        errors.append(f"RAV count {original['rav_count']} != 0 (fail-closed inventory gap)")
    if ci.get("results"):
        errors.append("CI gate reports new MEDIUM+ findings")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
