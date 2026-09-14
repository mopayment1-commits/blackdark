#!/usr/bin/env python3
"""Institutional readiness matrix — NIST SSDF + OWASP ASVS L2 + ISO 25010:2023 + project gates."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "INSTITUTIONAL_READINESS_MATRIX.json"


def _file_ok(*paths: str) -> bool:
    return all((ROOT / p).is_file() for p in paths)


def _run_pytest(targets: list[str]) -> bool:
    if not targets:
        return False
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *targets, "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _load_json(name: str) -> dict:
    p = ROOT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def build_matrix() -> dict:
    pre = _load_json("PRE_LAUNCH_GATE_ASSESSMENT.json")
    secrets = _load_json("SECRETS_HYGIENE_REPORT.json")
    wf_ok = _run_pytest(
        [
            "tests/test_security_workflow_register.py",
            "tests/test_d13_auth_abuse.py",
            "tests/test_codeql_cleartext_logging_closure.py",
        ]
    )
    mon_ok = _run_pytest(["tests/test_monitoring_alerting.py"])
    gov_spine_ok = _run_pytest(["tests/test_pre_launch_governance_spine.py"])

    # NIST SSDF v1.1 (SP 800-218) — outcome mapping (subset)
    nist_ssdf = {
        "PO_prepare_organization": {
            "PO.1_security_requirements_documented": _file_ok(
                "BLACKDARK_PRE_LAUNCH_INSTITUTIONAL_PLAN_AR_2026.md",
                "governing-sources-population/BLACKDARK_Institutional_Capability_Standard_2026_v6(1).md",
            ),
            "PO.3_toolchain_sast_deps": _file_ok(".github/workflows/security.yml", "scripts/secrets_hygiene_scan.py"),
            "PO.4_security_gates_in_pipeline": _file_ok(".github/workflows/ci.yml", "scripts/pre_launch_gate_assessor.py"),
            "status": "PARTIAL",
        },
        "PS_protect_software": {
            "PS.1_code_integrity_git": True,
            "PS.2_release_integrity": _file_ok("gate_verifier.py", "EVIDENCE_INDEX.json"),
            "PS.3_provenance_sbom": _file_ok("docs/data-room/sbom/"),
            "status": "PARTIAL",
        },
        "PW_produce_secure_software": {
            "PW.1_threat_modeling": _file_ok("docs/security/D13_VERIFICATION_MATRIX.md"),
            "PW.4_secure_coding_review": wf_ok,
            "PW.5_dynamic_testing": mon_ok,
            "status": "PARTIAL" if wf_ok else "FAIL",
        },
        "RV_respond_vulnerabilities": {
            "RV.1_vulnerability_tracking": _file_ok("docs/SECURITY_REMEDIATION.md", "critical_defects_closure.py"),
            "RV.2_incident_response": _file_ok("data/institutional_assurance/incident_response.json"),
            "status": "PARTIAL",
        },
    }

    # OWASP ASVS 4.0.3 Level 2 — representative controls
    asvs_l2 = {
        "V2_authentication": {
            "password_policy_mfa": _file_ok("mfa_service.py", "security_auth.py"),
            "anti_automation": _file_ok("security_middleware.py"),
            "tenant_isolation": wf_ok,
            "status": "PARTIAL" if wf_ok else "FAIL",
        },
        "V4_access_control": {
            "org_assert_access": wf_ok,
            "rbac_matrix": _file_ok("api/routers/institutional.py"),
            "status": "PARTIAL" if wf_ok else "FAIL",
        },
        "V7_logging": {
            "security_events": _file_ok("security_events.py"),
            "no_secret_logging": _run_pytest(["tests/test_codeql_cleartext_logging_closure.py"]),
            "status": "PARTIAL",
        },
        "V9_communication": {
            "tls_hsts_csp": _file_ok("security_middleware.py", "nginx/blackdark.conf"),
            "status": "PARTIAL",
        },
        "V13_api_security": {
            "openapi_errors": _file_ok("api/openapi_responses.py"),
            "rate_limiting": _file_ok("security_middleware.py"),
            "status": "PARTIAL",
        },
    }

    # ISO/IEC 25010:2023 — product quality characteristics
    iso25010 = {
        "functional_suitability": {
            "inventory_production_aligned": pre.get("honest_summary", {}).get("inventory_production_aligned", "114/826"),
            "pass_engineering_caps": "110/826 master",
            "status": "FAIL",
        },
        "reliability": {
            "health_probes": _file_ok("uptime_monitor.py", "ops/monitoring_alerting.py"),
            "uptime_self_probe": mon_ok,
            "status": "PARTIAL",
        },
        "security": {
            "secrets_hygiene": secrets.get("clean", False),
            "wf_remediated": wf_ok,
            "status": "PARTIAL" if secrets.get("clean") and wf_ok else "FAIL",
        },
        "maintainability": {
            "test_count_approx": "2800+",
            "ci_subset_only": True,
            "status": "PARTIAL",
        },
        "performance_efficiency": {
            "caching_configured": _file_ok("config.py"),
            "rate_limit_audit": _file_ok("FREE_API_RATE_LIMIT_AUDIT.json"),
            "status": "PARTIAL",
        },
    }

    gov11 = _load_json("GOVERNING_SPECS_11_VERIFICATION.json")
    gov_agg = gov11.get("aggregate") or {}
    gov11_ok = bool(gov_agg.get("all_11_specs_PASS_ENGINEERING"))

    # Project-specific: 11 governing specs + 826 capabilities
    project = {
        "governing_specs_avg_implementation_pct": gov_agg.get("implementation_pct_weighted", 18),
        "governing_specs_11_PASS_ENGINEERING": gov11_ok,
        "governing_specs_domains_strict_pass": gov_agg.get("domains_strict_pass", 0),
        "dts_implemented": pre.get("honest_summary", {}).get("dts_implemented", 12),
        "dat_implemented": pre.get("honest_summary", {}).get("dat_implemented", 5),
        "restore_ok": pre.get("honest_summary", {}).get("restore_ok", 10),
        "runtime_batch_826": pre.get("honest_summary", {}).get("runtime_batch_closure", "?"),
        "type_a_zero": False,
        "pre_launch_ready": pre.get("pre_launch_ready", False),
        "legal_pages": _file_ok("legal_content.py"),
        "monitoring_alerting": mon_ok,
        "governance_spine_tests": gov_spine_ok,
    }

    domains = [nist_ssdf, asvs_l2, iso25010]
    pass_count = sum(1 for d in domains for v in d.values() if isinstance(v, dict) and v.get("status") == "PASS")
    partial_count = sum(1 for d in domains for v in d.values() if isinstance(v, dict) and v.get("status") == "PARTIAL")
    fail_count = sum(1 for d in domains for v in d.values() if isinstance(v, dict) and v.get("status") == "FAIL")

    automatable_completion_pct = gov_agg.get("implementation_pct_weighted", 18)
    blocked_by = []
    if not gov11_ok:
        blocked_by.append("11 governing specs not all PASS_ENGINEERING")
    if not pre.get("pre_launch_ready", False):
        blocked_by.append("pre_launch gates not all PASS (826 inventory, E2E, CI)")
    if not project["type_a_zero"]:
        blocked_by.append("Type A buildable gaps remain in batches 04-17")
    if not _file_ok("tests/test_governing_specs_11_full.py"):
        blocked_by.append("governing specs test suite missing")

    maturity = min(
        100,
        int(
            (gov_agg.get("implementation_pct_weighted", 18) * 0.5)
            + (10 if wf_ok else 0)
            + (5 if secrets.get("clean") else 0)
            + (5 if mon_ok else 0)
            + (15 if gov11_ok else 0)
            + (10 if gov_spine_ok else 0)
        ),
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "frameworks": {
            "NIST_SSDF": {"publication": "NIST SP 800-218 v1.1", "url": "https://www.nist.gov/publications/secure-software-development-framework-ssdf-version-11"},
            "OWASP_ASVS": {"version": "4.0.3 Level 2", "url": "https://owasp.org/www-project-application-security-verification-standard/"},
            "ISO_25010": {"version": "2023", "url": "https://www.iso.org/standard/78176.html"},
            "PROJECT_V6": {"source": "BLACKDARK_Institutional_Capability_Standard_2026_v6"},
        },
        "nist_ssdf": nist_ssdf,
        "owasp_asvs_l2": asvs_l2,
        "iso_25010": iso25010,
        "project_specific": project,
        "summary": {
            "domain_status_counts": {"PASS": pass_count, "PARTIAL": partial_count, "FAIL": fail_count},
            "institutional_maturity_score_100": maturity,
            "final_goal_achieved": gov11_ok and bool(pre.get("pre_launch_ready", False)),
            "final_goal_blocked_by": blocked_by or ["none — automatable scope complete"],
            "excluded_from_scope": ["Railway deploy", "human pentest/SOC2", "vendor license contracts", "owner launch approval"],
            "automatable_backlog_priority": [
                "P0: engineering_audit_826 Type A closure + inventory reconcile",
                "P1: Playwright E2E critical paths",
                "P2: full CI green (2811 tests)",
                "P3: promote PARTIAL→IMPLEMENTED per domain with live evidence",
            ],
        },
    }


def main() -> int:
    matrix = build_matrix()
    OUT.write_text(json.dumps(matrix, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(matrix["summary"], indent=2, ensure_ascii=False))
    return 0 if matrix["summary"]["final_goal_achieved"] else 1


if __name__ == "__main__":
    sys.exit(main())
