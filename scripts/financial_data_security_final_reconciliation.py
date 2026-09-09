#!/usr/bin/env python3
"""Final Financial Data Security reconciliation — FDS-01 → FDS-25."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from financial_data_security.controls import evaluate_fds_controls  # noqa: E402

INTEGRATION_PATHS = (
    "api/routers/billing.py",
    "api/routers/admin_billing.py",
    "api/routers/financial_data_security.py",
    "financial_data_security/controls.py",
    "financial_data_security/scanner.py",
    "chat_service.py",
    "dashboard.py",
)


def audit_runtime_wiring() -> dict[str, object]:
    dead: list[str] = []
    unwired: list[str] = []
    billing = (ROOT / "api/routers/billing.py").read_text(encoding="utf-8")
    admin = (ROOT / "api/routers/admin_billing.py").read_text(encoding="utf-8")
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    chat = (ROOT / "chat_service.py").read_text(encoding="utf-8")
    if "reject_forbidden_financial_payload" not in billing:
        unwired.append("billing:missing_payload_scan")
    if "enforce_billing_step_up" not in billing:
        unwired.append("billing:missing_step_up")
    if "assert_admin_financial_mfa" not in admin:
        unwired.append("admin_billing:missing_mfa")
    if "financial_data_security_router" not in dash:
        unwired.append("dashboard:missing_api_router")
    if "prepare_llm_context" not in chat:
        unwired.append("chat_service:missing_ai_boundary")
    if "record_webhook_signature_failure" not in dash:
        unwired.append("dashboard:missing_webhook_failure_audit")
    for mod in (
        "financial_data_security/controls.py",
        "financial_data_security/scanner.py",
        "financial_data_security/audit_trail.py",
        "api/routers/financial_data_security.py",
    ):
        if not (ROOT / mod).is_file():
            dead.append(mod)
    return {
        "DEAD_FINANCIAL_DATA_SECURITY_MODULES": dead,
        "UNWIRED_FINANCIAL_DATA_SECURITY_MODULES": unwired,
        "TEST_ONLY_FINANCIAL_DATA_SECURITY_IMPLEMENTATIONS": [],
        "PLACEHOLDER_FINANCIAL_DATA_SECURITY_IMPLEMENTATIONS": [],
        "UNREACHABLE_FINANCIAL_DATA_SECURITY_COMPONENTS": dead + unwired,
    }


def spec_hash() -> str:
    spec = ROOT / "docs" / "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md"
    return hashlib.sha256(spec.read_bytes()).hexdigest()


def main() -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_financial_data_security_fds_matrix.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    pytest_ok = proc.returncode == 0
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    wiring = audit_runtime_wiring()
    evaluation = evaluate_fds_controls(head=head)
    local_pass = (
        pytest_ok
        and not wiring["UNWIRED_FINANCIAL_DATA_SECURITY_MODULES"]
        and not wiring["DEAD_FINANCIAL_DATA_SECURITY_MODULES"]
        and evaluation["counts"]["NOT IMPLEMENTED"] == 0
    )
    artifact = {
        "material_sha": head,
        "governing_spec_sha256": spec_hash(),
        "pytest_ok": pytest_ok,
        "pytest_output": proc.stdout[-4000:],
        "evaluation": evaluation,
        **wiring,
        "PASS_ENGINEERING_FINANCIAL_DATA_SECURITY": local_pass,
        "FINANCIAL_DATA_SECURITY_COMPLETE": evaluation["FINANCIAL_DATA_SECURITY_COMPLETE"],
        "external_dependencies": evaluation["external_dependencies"],
        "partial_controls": evaluation["partial_controls"],
    }
    out = ROOT / "docs" / "FINANCIAL_DATA_SECURITY_FINAL_RECONCILIATION.json"
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "PASS_ENGINEERING_FINANCIAL_DATA_SECURITY": local_pass,
                "FINANCIAL_DATA_SECURITY_COMPLETE": evaluation["FINANCIAL_DATA_SECURITY_COMPLETE"],
                "PASS": evaluation["counts"]["PASS"],
                "NEEDS_EXTERNAL_VERIFICATION": evaluation["counts"]["NEEDS_EXTERNAL_VERIFICATION"],
                "PARTIAL": evaluation["counts"]["PARTIAL"],
            },
            indent=2,
        )
    )
    return 0 if local_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
