"""Launch-57 external assurance closure status (honest, not certifying)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def launch57_closure_status() -> dict[str, Any]:
    from pentest_attestation import pentest_attestation_status, verify_pentest_attestation
    from webauthn_service import webauthn_status

    root = Path(__file__).resolve().parent
    security_txt = root / "static" / ".well-known" / "security.txt"
    waf_rules = root / "deploy" / "cloudflare" / "waf-rules.json"
    pentest = pentest_attestation_status()
    edge_active = bool(
        os.getenv("CDN_WAF_ACTIVE", "").strip() or os.getenv("CLOUDFLARE_ZONE_ID", "").strip()
    )

    from launch57_completion_status import completion_status_attachment

    inventory = completion_status_attachment()
    return {
        "program": "LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION",
        "baseline_sha": "e73f398d4048723bd10670beab14a0d18ceb19ef",
        "evidence_index": "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json",
        "cisa_certification_claimed": False,
        "cisa_remediation_inventory": inventory,
        "findings": {
            "pentest_attestation": {
                "status": "CLOSED" if verify_pentest_attestation() else "OPEN",
                "detail": pentest,
                "ops_runbook": "docs/ops/PENTEST_ENGAGEMENT_RUNBOOK.md",
                "deposit_guide": "docs/evidence/PENTEST_DEPOSIT_LAUNCH57.md",
                "deposit_api": "POST /api/institutional/pentest/deposit",
            },
            "waf_cdn_edge": {
                "status": "CLOSED" if edge_active else "OPEN",
                "edge_active": edge_active,
                "rules_template_present": waf_rules.is_file(),
                "ops_runbook": "docs/ops/EDGE_WAF_ACTIVATION_RUNBOOK.md",
                "checklist": "docs/CDN_WAF_CHECKLIST.md",
            },
            "security_txt": {
                "status": "CLOSED_REPO" if security_txt.is_file() else "OPEN",
                "repo_path": str(security_txt),
                "verify_script": "scripts/verify_well_known_security_txt.py",
            },
            "secure_by_design_pledge": {
                "status": "OPEN_EXECUTIVE",
                "package": "docs/governance/SECURE_BY_DESIGN_PLEDGE_SUBMISSION_PACKAGE.md",
            },
            "phishing_resistant_auth": webauthn_status(),
        },
        "verification_scripts": [
            "scripts/launch57_closure_report.py",
            "scripts/verify_launch57_external_assurance.py",
            "scripts/verify_launch57_prod_surface.py",
            "scripts/verify_well_known_security_txt.py",
            "scripts/verify_edge_waf_cdn.py",
        ],
        "open_findings_register": "governance/launch57/LAUNCH57_OPEN_FINDINGS_REGISTER.md",
    }
