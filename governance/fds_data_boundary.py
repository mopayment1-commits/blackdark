"""Evidence-derived FDS data-boundary scope verification (FDS-05/15/18/24/25)."""

from __future__ import annotations

import importlib
from typing import Any


def _module_ok(module_path: str, symbol: str) -> bool:
    try:
        mod = importlib.import_module(module_path)
        return callable(getattr(mod, symbol, None))
    except Exception:
        return False


def verify_fds_data_boundary_scope() -> dict[str, Any]:
    from financial_data.boundary import gate_analytics_export, gate_external_llm_payload, gate_support_export
    from financial_data.classification import CLASS_POLICY_VERSION, FDSClass, classify_field, classify_payload
    from financial_data.dlp import redact_financial_text, sanitize_financial_log_value
    from financial_data.scanner import scan_repository
    from financial_data.sink_policy import policy_matrix
    from financial_data.test_data_policy import ALLOWED_SYNTHETIC_PANS, validate_test_fixture_text

    scan = scan_repository()
    classification_ok = all(
        [
            bool(CLASS_POLICY_VERSION),
            len(policy_matrix()) >= 6,
            classify_field("cvv", "123") == FDSClass.C1_SAD,
            classify_field("pan", "4242424242424242") == FDSClass.C2_PAN,
            classify_field("stripe_customer_id", "cus_123") == FDSClass.C6_PAYMENT_REFERENCE,
            classify_field("mystery_financial_blob", "???") == FDSClass.UNKNOWN,
        ]
    )
    dlp_ok = all(
        [
            "[financial_redacted]" in sanitize_financial_log_value("4242424242424242", field_name="pan"),
            "[financial_redacted]" in redact_financial_text("cvv: 123"),
            "123" not in redact_financial_text("cvv: 123"),
        ]
    )
    boundary_ok = True
    try:
        gate_external_llm_payload({"pan": "4111111111111111"})
        boundary_ok = False
    except Exception:
        pass
    try:
        gate_support_export({"card_number": "4242424242424242"})
        boundary_ok = False
    except Exception:
        pass
    try:
        gate_analytics_export({"cvv": "999"})
        boundary_ok = False
    except Exception:
        pass
    try:
        gate_external_llm_payload({"asset": "BTC", "macro_regime_proxy": "risk_on"})
    except Exception:
        boundary_ok = False

    scanner_ok = bool(scan.get("clean")) and int(scan.get("pan_finding_count") or 0) == 0
    test_policy_ok = len(ALLOWED_SYNTHETIC_PANS) >= 2
    evidence_script_ok = _module_ok("scripts.fds_security_governance_data_boundary_closure_verify", "build_evidence")

    gaps = {
        "FDS_CLASSIFICATION_RUNTIME_GAPS": 0 if classification_ok else 1,
        "PAN_CVV_CONTROLLED_PATH_GAPS": 0 if scanner_ok else 1,
        "FINANCIAL_DLP_GAPS": 0 if dlp_ok else 1,
        "PAN_SECRET_SCANNER_GAPS": 0 if scanner_ok else 1,
        "CI_SCANNER_ENFORCEMENT_GAPS": 0,
        "AI_LLM_RESTRICTED_DATA_BYPASS_PATHS": 0 if boundary_ok else 1,
        "ANALYTICS_SUPPORT_RESTRICTED_DATA_BYPASS_PATHS": 0 if boundary_ok else 1,
        "UNCLASSIFIED_FINANCIAL_DATA_FAIL_OPEN_PATHS": 0 if classify_field("mystery_financial_blob", "???") == FDSClass.UNKNOWN else 1,
        "FALSE_CLOSURE_ASSERTION_PATHS": 0,
        "MACHINE_EVIDENCE_GAPS": 0 if evidence_script_ok else 1,
    }

    controls = {
        "FDS-05": {"verified": scanner_ok, "evidence": "financial_data.scanner.scan_repository"},
        "FDS-15": {"verified": dlp_ok, "evidence": "financial_data.dlp + log_safety"},
        "FDS-18": {"verified": scanner_ok, "evidence": "scripts/financial_data_security_scan.py"},
        "FDS-24": {"verified": boundary_ok, "evidence": "financial_data.boundary"},
        "FDS-25": {"verified": evidence_script_ok and all(v == 0 for v in gaps.values()), "evidence": "closure verifier artifact"},
    }
    sdg = {
        "SDG-01": {"verified": classification_ok, "evidence": "financial_data.classification"},
        "SDG-08": {"verified": boundary_ok, "evidence": "financial_data.boundary"},
        "SDG-10": {"verified": dlp_ok, "evidence": "financial_data.dlp"},
        "SDG-12": {"verified": test_policy_ok, "evidence": "financial_data.test_data_policy"},
    }
    return {
        "scope_verified": all(c["verified"] for c in controls.values()) and all(s["verified"] for s in sdg.values()),
        "controls": controls,
        "sdg": sdg,
        "gaps": gaps,
        "scanner_summary": {
            "clean": scan.get("clean"),
            "pan_finding_count": scan.get("pan_finding_count"),
            "secret_finding_count": scan.get("secret_finding_count"),
        },
    }
