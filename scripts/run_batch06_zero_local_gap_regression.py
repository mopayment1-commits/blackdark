#!/usr/bin/env python3
"""Full cross-batch regression for Batch06 zero-local-gap institutional closure."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BATCH06_CROSS_BATCH_REGRESSION.json"


def run_pytest(paths: list[str], label: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *paths, "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    tail = (proc.stdout or "") + (proc.stderr or "")
    passed_line = [ln for ln in tail.splitlines() if "passed" in ln and ("failed" in ln or "error" in ln or ln.strip().endswith("passed"))]
    return {
        "label": label,
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "summary": passed_line[-1] if passed_line else tail.strip()[-200:],
    }


def run_script(name: str, label: str) -> dict[str, Any]:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / name)], cwd=ROOT, capture_output=True, text=True)
    ok = proc.returncode == 0
    payload: dict[str, Any] = {"label": label, "script": name, "exit_code": proc.returncode, "passed": ok}
    if name == "run_batch_verification_orchestrator.py":
        out_path = ROOT / "docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json"
        if out_path.is_file():
            doc = json.loads(out_path.read_text(encoding="utf-8"))
            payload["all_verified"] = doc.get("all_verified")
            ok = ok and bool(doc.get("all_verified"))
            payload["passed"] = ok
    return payload


def main() -> None:
    suites: list[dict[str, Any]] = []

    suites.append(run_script("verify_batch01_http_all50.py", "batch01_http_all50"))
    suites.append(run_script("verify_official_batch02_production.py", "batch02_official_production"))
    suites.append(run_script("run_batch_verification_orchestrator.py", "batch_verification_orchestrator"))

    pytest_groups = [
        (["tests/cap646/test_batch01_dedicated.py", "tests/cap646/test_batch01_production.py"], "batch01"),
        (["tests/cap646/test_batch03_gateway_canonical_entitlement_contract.py"], "batch03_gateway"),
        (["tests/cap646/test_batch04_gateway_canonical_entitlement_contract.py"], "batch04_gateway"),
        (
            [
                "tests/cap646/test_batch05_v2_assurance.py",
                "tests/cap646/test_batch05_local_assurance_freeze.py",
                "tests/cap646/test_batch05_prep_dedicated.py",
                "tests/cap646/test_batch05_gateway_canonical_entitlement_contract.py",
            ],
            "batch05_frozen",
        ),
        (
            [
                "tests/cap646/test_batch06_ids_contract.py",
                "tests/cap646/test_batch06_strangler_spine.py",
                "tests/cap646/test_batch06_acceptance_contract.py",
                "tests/cap646/test_batch06_v2_assurance.py",
            ],
            "batch06",
        ),
        (["tests/cap646/test_ci_deterministic_closure.py"], "shared_runtime_service_bus"),
        (["tests/test_pentagonal_hero_binding.py"], "six_heroes"),
    ]
    for paths, label in pytest_groups:
        suites.append(run_pytest(paths, label))

    failed = [s for s in suites if not s["passed"]]
    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "suites": suites,
        "failed": [s["label"] for s in failed],
        "partial": [],
        "material_skipped": [],
        "known_flaky_unresolved": [],
        "full_pass": len(failed) == 0,
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"full_pass": doc["full_pass"], "failed": doc["failed"]}, indent=2))
    if not doc["full_pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
