#!/usr/bin/env python3
"""Regression impact matrix for Adaptive v4 changes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_REGRESSION_IMPACT_MATRIX.json"

MODULES = [
    {
        "module": "bd_platform/adaptive_intelligence/",
        "subsystem": "adaptive_v4_runtime",
        "dependents": ["api/routers/adaptive_intelligence.py", "governance/adaptive_ux_governance.py", "dashboard.py"],
        "tests": [
            "tests/test_adaptive_v4_closure.py",
            "tests/test_adaptive_v4_falsification.py",
            "tests/test_adaptive_v4_security.py",
            "tests/test_adaptive_v4_a11y_interaction.py",
            "tests/test_adaptive_v4_browser_a11y.py",
            "tests/test_adaptive_v4_performance.py",
        ],
        "reason": "Direct adaptive implementation",
    },
    {
        "module": "api/routers/adaptive_intelligence.py",
        "subsystem": "api_routing",
        "dependents": ["dashboard.py"],
        "tests": ["tests/test_adaptive_v4_security.py", "tests/test_adaptive_v4_performance.py"],
        "reason": "New API surface",
    },
    {
        "module": "governance/adaptive_ux_requirements.py",
        "subsystem": "governance_spine",
        "dependents": ["scripts/governing_specs_11_verifier.py"],
        "tests": ["tests/test_pre_launch_governance_spine.py", "tests/test_governing_specs_11_full.py"],
        "reason": "AIE spine runtime verification",
    },
    {
        "module": "decision_truth/ (reuse)",
        "subsystem": "decision_truth",
        "dependents": ["bd_platform/adaptive_intelligence/decision_contract.py"],
        "tests": ["tests/test_decision_truth_pipeline.py"],
        "reason": "Canonical decision contract reuse",
    },
    {
        "module": "cap646/entitlements.py (reuse)",
        "subsystem": "entitlement",
        "dependents": ["bd_platform/adaptive_intelligence/entitlement_gate.py"],
        "tests": ["tests/cap646/test_get_entitlement.py"],
        "reason": "Entitlement authority reuse",
    },
    {
        "module": "blackdark/data_governance/ (reuse)",
        "subsystem": "data_governance",
        "dependents": [],
        "tests": ["tests/test_data_governance_runtime_enforcement.py"],
        "reason": "Evidence class / runtime integration path",
    },
    {
        "module": "intent_router.py (reuse)",
        "subsystem": "intent",
        "dependents": ["bd_platform/adaptive_intelligence/intent_contract.py"],
        "tests": ["tests/test_trust_os_lenses_ux.py"],
        "reason": "Intent resolution reuse",
    },
]


def _run_suite(path: str) -> dict:
    env = dict(**__import__("os").environ)
    if "browser_a11y" in path:
        venv_site = ROOT / ".venv-a11y" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        if venv_site.is_dir():
            env["PYTHONPATH"] = f"{venv_site}:{env.get('PYTHONPATH', '')}"
        env["A11Y_TEST_PORT"] = "8770"
    args = [sys.executable, "-m", "pytest", path, "-q", "--tb=no"]
    if "browser_a11y" in path:
        args.append("--noconftest")
    proc = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    out = proc.stdout + proc.stderr
    passed = proc.returncode == 0
    return {"path": path, "exit_code": proc.returncode, "passed": passed, "summary": out.strip().split("\n")[-1] if out else ""}


def main() -> None:
    rows = []
    all_tests: set[str] = set()
    for m in MODULES:
        results = [_run_suite(t) for t in m["tests"]]
        all_tests.update(m["tests"])
        rows.append({**m, "test_results": results, "all_passed": all(r["passed"] for r in results)})
    payload = {
        "modules": rows,
        "unique_test_suites": sorted(all_tests),
        "AFFECTED_MODULES_WITHOUT_REGRESSION_COVERAGE": sum(1 for r in rows if not r["all_passed"]),
        "FULL_RELEVANT_REGRESSION_GREEN": all(r["all_passed"] for r in rows),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"modules": len(rows), "green": payload["FULL_RELEVANT_REGRESSION_GREEN"]}, indent=2))
    return 0 if payload["FULL_RELEVANT_REGRESSION_GREEN"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
