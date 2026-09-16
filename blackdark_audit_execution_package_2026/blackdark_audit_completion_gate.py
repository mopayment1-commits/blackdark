#!/usr/bin/env python3
"""Preflight and completion gate for BLACKDARK audit execution package.
Does NOT invent procedures — validates SSOT files only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "BLACKDARK_AUDIT_REQUIREMENTS_2026.yaml",
    "BLACKDARK_AUDIT_PROCEDURES_2026.yaml",
    "BLACKDARK_AUDIT_STATE_2026.yaml",
    "BLACKDARK_CURSOR_EXECUTION_MANDATE_2026.md",
]


def load_yaml_count(path: Path, key: str) -> int | None:
    if not path.exists():
        return None
    try:
        import yaml  # type: ignore
    except ImportError:
        text = path.read_text(encoding="utf-8")
        # minimal count for list items starting with "  - id:" or "- id:"
        return text.count("\n  - id:") + text.count("\n- id:")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for k in (key, "requirements", "procedures", "items"):
            if k in data and isinstance(data[k], list):
                return len(data[k])
    return None


def run_preflight() -> dict:
    structural_errors: list[str] = []
    for name in REQUIRED:
        if not (ROOT / name).exists():
            structural_errors.append(f"MISSING: {name}")

    req_path = ROOT / "BLACKDARK_AUDIT_REQUIREMENTS_2026.yaml"
    proc_path = ROOT / "BLACKDARK_AUDIT_PROCEDURES_2026.yaml"

    requirements = load_yaml_count(req_path, "requirements") if req_path.exists() else 0
    procedures = load_yaml_count(proc_path, "procedures") if proc_path.exists() else 0
    mapped = procedures if req_path.exists() and proc_path.exists() else 0

    if req_path.exists() and procedures != requirements:
        structural_errors.append(f"COUNT_MISMATCH: requirements={requirements} procedures={procedures}")
    if requirements != 354:
        structural_errors.append(f"REQUIREMENTS_COUNT: expected 354 got {requirements or 'MISSING'}")
    if procedures != 354:
        structural_errors.append(f"PROCEDURES_COUNT: expected 354 got {procedures or 'MISSING'}")
    if mapped != 354:
        structural_errors.append(f"MAPPED: expected 354 got {mapped or 0}")

    gate = "PASS" if not structural_errors and requirements == 354 and procedures == 354 else "FAIL"
    return {
        "requirements": requirements or 0,
        "procedures": procedures or 0,
        "mapped_requirements": mapped or 0,
        "structural_errors": structural_errors,
        "PREFLIGHT_GATE": gate,
    }


def run_completion(state_path: Path) -> dict:
    pre = run_preflight()
    if pre["PREFLIGHT_GATE"] != "PASS":
        return {**pre, "AUDIT_COMPLETION_GATE": "FAIL", "reason": "preflight not pass"}

    # Full completion requires STATE with all 354 procedures closed
    if not state_path.exists():
        return {**pre, "AUDIT_COMPLETION_GATE": "FAIL", "reason": "state incomplete"}

    try:
        import yaml  # type: ignore
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {**pre, "AUDIT_COMPLETION_GATE": "FAIL", "reason": str(exc)}

    results = state.get("procedure_results") or state.get("results") or {}
    total = state.get("procedures_total", 354)
    closed = sum(
        1 for v in (results.values() if isinstance(results, dict) else [])
        if isinstance(v, dict) and v.get("status") in ("PASS", "FAIL", "PARTIAL", "BLOCKED", "NOT_APPLICABLE")
    )
    passes = state.get("ten_passes_complete", False)
    ok = closed >= total and passes and pre["PREFLIGHT_GATE"] == "PASS"
    return {
        **pre,
        "procedures_closed": closed,
        "procedures_total": total,
        "ten_passes_complete": passes,
        "AUDIT_COMPLETION_GATE": "PASS" if ok else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = run_preflight()
    else:
        result = run_completion(ROOT / "BLACKDARK_AUDIT_STATE_2026.yaml")
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("PREFLIGHT_GATE") == "PASS" or result.get("AUDIT_COMPLETION_GATE") == "PASS" else 1)


if __name__ == "__main__":
    main()
