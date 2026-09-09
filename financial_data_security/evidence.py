"""Machine-verifiable evidence collector for FDS controls."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def collect_fds_evidence(*, head: str | None = None) -> dict[str, Any]:
    if head is None:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    from financial_data_security.ai_boundary import ai_boundary_status
    from financial_data_security.audit_trail import verify_audit_chain
    from financial_data_security.environment import environment_isolation_status
    from financial_data_security.fips_policy import fips_path_status
    from financial_data_security.incident import run_incident_drill
    from financial_data_security.retention import retention_status
    from financial_data_security.scanner import scan_repository_paths
    from financial_data_security.secrets import secret_manager_status
    from financial_data_security.service_identities import service_identity_status
    from financial_data_security.tls_policy import tls_policy_status
    from financial_data_security.webhooks import webhook_security_status
    from payments_usd import SECURITY_POSTURE, payments_architecture

    return {
        "head": head,
        "payments_architecture": payments_architecture(),
        "security_posture": SECURITY_POSTURE,
        "repo_pan_scan": scan_repository_paths(),
        "secret_manager": secret_manager_status(),
        "environment_isolation": environment_isolation_status(),
        "webhook_security": webhook_security_status(),
        "audit_chain": verify_audit_chain(),
        "retention": retention_status(),
        "incident_drill": run_incident_drill(),
        "ai_boundary": ai_boundary_status(),
        "service_identities": service_identity_status(),
        "tls_policy": tls_policy_status(),
        "fips_policy": fips_path_status(),
    }
