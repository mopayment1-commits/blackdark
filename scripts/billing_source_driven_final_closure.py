#!/usr/bin/env python3
"""Billing source-driven final closure — rebuild ledger, run tests, emit freeze."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bd_platform.billing_source_driven_engineering import billing_source_driven_status  # noqa: E402

LEDGER = ROOT / "docs/BILLING_IMPLEMENTATION_LEDGER.json"
FREEZE = ROOT / "docs/BILLING_SOURCE_DRIVEN_FINAL_FREEZE.json"
SPEC = ROOT / "docs/BLACKDARK_INSTITUTIONAL_BILLING_SUBSCRIPTION_ENTITLEMENT_SPEC_v1.md"
BRANCH = "cursor/billing-institutional-closure-ed16"

PYTEST_SUITES = [
    ("billing_subscription_engine", ["tests/test_billing_subscription_engine.py"]),
    ("billing_p0_matrix", ["tests/test_billing_p0_test_matrix.py"]),
    ("billing_source_driven", ["tests/test_billing_source_driven_engineering.py"]),
    ("payments_security", ["tests/test_payments_usd_security.py"]),
]


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pytest() -> dict:
    ok = True
    suites = []
    for label, paths in PYTEST_SUITES:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", *paths, "-q", "--tb=short"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        suites.append({"label": label, "ok": proc.returncode == 0, "paths": paths})
        ok = ok and proc.returncode == 0
    return {"ok": ok, "suites": suites}


def main() -> None:
    # Build universe + index if missing
    subprocess.run([sys.executable, str(ROOT / "scripts/billing_full_source_decomposition.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_billing_implementation_index.py")], check=True)

    pytest = run_pytest()
    head = git_head()
    status = billing_source_driven_status(head=head, pytest_ok=pytest["ok"])

    ledger = {
        "schema_version": "1.0",
        "spec_file": SPEC.name,
        "spec_version": "Final Consolidated & Reconciled v1.0",
        "source_of_truth_rule": "The specification file is authoritative; this ledger is tracking only.",
        "last_closure_sha": head,
        "last_closure_at": datetime.now(UTC).isoformat(),
        "requirements": status["requirements"],
    }
    LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    freeze = {
        "branch": BRANCH,
        "material_sha": head,
        "spec_sha256": file_sha256(SPEC),
        "ledger_sha256": file_sha256(LEDGER),
        "closed_at": datetime.now(UTC).isoformat(),
        "pytest": pytest,
        **{k: v for k, v in status.items() if k != "requirements"},
    }
    FREEZE.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"PASS_ENGINEERING": status["PASS_ENGINEERING"], "pytest_ok": pytest["ok"]}, indent=2))
    if not pytest["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
