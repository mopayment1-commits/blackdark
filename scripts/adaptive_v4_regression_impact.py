#!/usr/bin/env python3
"""Gate 5 — regression impact classification for Adaptive v4 changes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_REGRESSION_IMPACT_MATRIX.json"

ADAPTIVE_CHANGED = [
    {
        "module": "bd_platform/adaptive_intelligence/",
        "change_type": "new_implementation",
        "direct_dependents": ["api/routers/adaptive_intelligence.py", "governance/adaptive_ux_governance.py", "dashboard.py"],
        "critical_indirect_dependents": ["templates/landing.html", "templates/utility.html"],
        "tests": [
            "tests/test_adaptive_v4_closure.py",
            "tests/test_adaptive_v4_falsification.py",
            "tests/test_adaptive_v4_security.py",
            "tests/test_adaptive_v4_a11y_interaction.py",
            "tests/test_adaptive_v4_browser_a11y.py",
            "tests/test_adaptive_v4_performance.py",
        ],
    },
    {
        "module": "api/routers/adaptive_intelligence.py",
        "change_type": "new_api_surface",
        "direct_dependents": ["dashboard.py"],
        "critical_indirect_dependents": [],
        "tests": ["tests/test_adaptive_v4_security.py", "tests/test_adaptive_v4_performance.py"],
    },
    {
        "module": "governance/adaptive_ux_requirements.py",
        "change_type": "governance_spine_extension",
        "direct_dependents": ["scripts/governing_specs_11_verifier.py"],
        "critical_indirect_dependents": ["governance/adaptive_ux_governance.py"],
        "tests": ["tests/test_pre_launch_governance_spine.py", "tests/test_governing_specs_11_full.py"],
    },
    {
        "module": "governance/adaptive_ux_governance.py",
        "change_type": "governance_runtime",
        "direct_dependents": ["bd_platform/adaptive_intelligence/"],
        "critical_indirect_dependents": [],
        "tests": ["tests/test_adaptive_v4_closure.py"],
    },
    {
        "module": "templates/landing.html",
        "change_type": "a11y_remediation",
        "direct_dependents": ["dashboard.py"],
        "critical_indirect_dependents": [],
        "tests": ["tests/test_adaptive_v4_browser_a11y.py", "tests/test_adaptive_v4_a11y_interaction.py"],
    },
    {
        "module": "templates/utility.html",
        "change_type": "a11y_remediation",
        "direct_dependents": ["dashboard.py"],
        "critical_indirect_dependents": [],
        "tests": ["tests/test_adaptive_v4_browser_a11y.py"],
    },
]

CANONICAL_AFFECTED = [
    {
        "module": "decision_truth/ (reuse)",
        "change_type": "canonical_reuse",
        "direct_dependents": ["bd_platform/adaptive_intelligence/decision_contract.py"],
        "critical_indirect_dependents": [],
        "tests": ["tests/test_decision_truth_pipeline.py"],
    },
    {
        "module": "cap646/entitlements.py (reuse)",
        "change_type": "canonical_reuse",
        "direct_dependents": ["bd_platform/adaptive_intelligence/entitlement_gate.py"],
        "critical_indirect_dependents": [],
        "tests": ["tests/cap646/test_get_entitlement.py"],
    },
    {
        "module": "blackdark/data_governance/ (reuse)",
        "change_type": "canonical_reuse",
        "direct_dependents": [],
        "critical_indirect_dependents": ["bd_platform/adaptive_intelligence/decision_contract.py"],
        "tests": ["tests/test_data_governance_runtime_enforcement.py"],
    },
    {
        "module": "intent_router.py (reuse)",
        "change_type": "canonical_reuse",
        "direct_dependents": ["bd_platform/adaptive_intelligence/intent_contract.py"],
        "critical_indirect_dependents": ["bd_platform/adaptive_intelligence/intelligence_router.py"],
        "tests": ["tests/test_trust_os_lenses_ux.py"],
    },
]


def _run_suite(path: str) -> dict[str, Any]:
    import os

    env = dict(**os.environ)
    if "browser_a11y" in path:
        venv_site = ROOT / ".venv-a11y" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        if venv_site.is_dir():
            env["PYTHONPATH"] = f"{venv_site}:{env.get('PYTHONPATH', '')}"
        env["A11Y_TEST_PORT"] = "8772"
    args = [sys.executable, "-m", "pytest", path, "-q", "--tb=no"]
    if "browser_a11y" in path:
        args.append("--noconftest")
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, env=env)
    out = proc.stdout + proc.stderr
    return {
        "path": path,
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "summary": out.strip().split("\n")[-1] if out else "",
    }


def _process_modules(modules: list[dict[str, Any]], cache: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for m in modules:
        results = []
        for t in m["tests"]:
            if t not in cache:
                cache[t] = _run_suite(t)
            results.append(cache[t])
        rows.append({**m, "test_results": results, "all_passed": all(r["passed"] for r in results)})
    return rows


def main() -> int:
    cache: dict[str, dict[str, Any]] = {}
    adaptive_rows = _process_modules(ADAPTIVE_CHANGED, cache)
    canonical_rows = _process_modules(CANONICAL_AFFECTED, cache)
    all_rows = adaptive_rows + canonical_rows

    ui_api = [r for r in adaptive_rows if "api/" in r["module"] or "templates/" in r["module"]]
    persistence_gov = [r for r in all_rows if "governance/" in r["module"] or "data_governance" in r["module"]]

    changed_without_coverage = sum(1 for r in adaptive_rows if not r["all_passed"])
    canonical_without_coverage = sum(1 for r in canonical_rows if not r["all_passed"])
    all_tests: set[str] = set()
    for r in all_rows:
        all_tests.update(r["tests"])

    payload = {
        "impact_classification": {
            "adaptive_production_modules_changed": len(adaptive_rows),
            "canonical_external_modules_affected": len(canonical_rows),
            "ui_api_modules_affected": len(ui_api),
            "persistence_governance_modules_affected": len(persistence_gov),
            "total_affected_modules": len(all_rows),
            "clarification": "Prior '7 affected modules' referred to total changed+affected surface (adaptive + canonical reuse), not canonical-only count.",
        },
        "adaptive_production_modules": adaptive_rows,
        "canonical_external_modules": canonical_rows,
        "ui_api_modules": ui_api,
        "persistence_governance_modules": persistence_gov,
        "unique_test_suites_executed": sorted(all_tests),
        "CHANGED_PRODUCTION_MODULES_WITHOUT_TEST_COVERAGE": changed_without_coverage,
        "AFFECTED_CANONICAL_MODULES_WITHOUT_REGRESSION_COVERAGE": canonical_without_coverage,
        "UNRESOLVED_RELEVANT_REGRESSION_FAILURES": changed_without_coverage + canonical_without_coverage,
        "FULL_RELEVANT_REGRESSION_GREEN": all(r["all_passed"] for r in all_rows),
        "AFFECTED_MODULES_WITHOUT_REGRESSION_COVERAGE": changed_without_coverage + canonical_without_coverage,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "adaptive_changed": payload["impact_classification"]["adaptive_production_modules_changed"],
                "canonical_affected": payload["impact_classification"]["canonical_external_modules_affected"],
                "FULL_RELEVANT_REGRESSION_GREEN": payload["FULL_RELEVANT_REGRESSION_GREEN"],
            },
            indent=2,
        )
    )
    return 0 if payload["FULL_RELEVANT_REGRESSION_GREEN"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
