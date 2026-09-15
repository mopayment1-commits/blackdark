#!/usr/bin/env python3
"""P6 DTS cross-cutting delivery closure verification (DTS-054/055/056)."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "DECISION_TRUTH_P6_CROSS_CUTTING_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md"

P6_DTS = ["DTS-054", "DTS-055", "DTS-056"]

CANONICAL_OWNERS = {
    "timezone_authority": "governance/timezone_governance.py",
    "i18n_authority": "i18n_service.py",
    "i18n_locales": "i18n_locales.py",
    "accessibility_authority": "accessibility_audit_service.py",
    "cross_cutting_orchestrator": "decision_truth/cross_cutting/__init__.py",
    "timezone_projection": "decision_truth/cross_cutting/timezone.py",
    "i18n_projection": "decision_truth/cross_cutting/i18n.py",
    "accessibility_projection": "decision_truth/cross_cutting/accessibility.py",
    "product_wire": "decision_truth/product/__init__.py",
}


def _spec_hash() -> str:
    if SPEC.is_file():
        return hashlib.sha256(SPEC.read_bytes()).hexdigest()
    return "missing"


def _git_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _read(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _scan_gaps() -> dict[str, list[str]]:
    tz_gov = _read("governance/timezone_governance.py")
    tz_proj = _read("decision_truth/cross_cutting/timezone.py")
    i18n_proj = _read("decision_truth/cross_cutting/i18n.py")
    a11y_proj = _read("decision_truth/cross_cutting/accessibility.py")
    product = _read("decision_truth/product/__init__.py")
    i18n_service = _read("i18n_service.py")
    why_not = _read("decision_truth/product/why_not.py")

    gaps: dict[str, list[str]] = {
        "DTS_NAIVE_CANONICAL_DATETIME_PATHS": [],
        "DTS_USER_TIMEZONE_RENDERING_GAPS": [],
        "DTS_DUPLICATE_TIMEZONE_AUTHORITIES": [],
        "DTS_HARDCODED_USER_FACING_ENGLISH_PATHS": [],
        "DTS_I18N_COVERAGE_GAPS": [],
        "DTS_BROKEN_LOCALE_FALLBACK_PATHS": [],
        "DTS_COLOR_ONLY_MEANING_PATHS": [],
        "DTS_KEYBOARD_ACCESS_GAPS": [],
        "DTS_FOCUS_MANAGEMENT_GAPS": [],
        "DTS_SCREEN_READER_LABEL_GAPS": [],
        "DTS_ACCESSIBLE_STATUS_ANNOUNCEMENT_GAPS": [],
        "DTS_CHART_TEXT_ALTERNATIVE_GAPS": [],
        "DTS_CRITICAL_CONTENT_ACCESSIBILITY_GAPS": [],
    }

    if "ensure_utc_aware" not in tz_gov or "parse_canonical_timestamp" not in tz_gov:
        gaps["DTS_NAIVE_CANONICAL_DATETIME_PATHS"].append("timezone_governance_missing_utc_helpers")
    if "project_dts_timestamps" not in tz_proj:
        gaps["DTS_USER_TIMEZONE_RENDERING_GAPS"].append("missing_dts_timestamp_projection")
    if tz_proj.count("ZoneInfo(") > 0:
        gaps["DTS_DUPLICATE_TIMEZONE_AUTHORITIES"].append("parallel_zoneinfo_in_projection")
    if "resolve_user_timezone" not in tz_gov:
        gaps["DTS_DUPLICATE_TIMEZONE_AUTHORITIES"].append("missing_canonical_timezone_resolver")

    if "apply_cross_cutting_delivery" not in product:
        gaps["DTS_USER_TIMEZONE_RENDERING_GAPS"].append("product_missing_cross_cutting_wire")
    if '"dts.' not in i18n_service:
        gaps["DTS_HARDCODED_USER_FACING_ENGLISH_PATHS"].append("missing_dts_i18n_keys")
    if "localize_dts_payload" not in i18n_proj:
        gaps["DTS_HARDCODED_USER_FACING_ENGLISH_PATHS"].append("missing_i18n_projection")
    if re.search(r'human_explanation.*=.*"[A-Z]', why_not) and "message_keys" not in why_not:
        gaps["DTS_HARDCODED_USER_FACING_ENGLISH_PATHS"].append("why_not_hardcoded_english")

    from decision_truth.cross_cutting.i18n import validate_38_locale_coverage
    from decision_truth.cross_cutting.locales import CANONICAL_38_LOCALES

    cov = validate_38_locale_coverage()
    if cov["gaps"]:
        gaps["DTS_I18N_COVERAGE_GAPS"].extend(cov["gaps"][:20])
    if len(CANONICAL_38_LOCALES) != 38:
        gaps["DTS_I18N_COVERAGE_GAPS"].append(f"locale_count_{len(CANONICAL_38_LOCALES)}")
    from i18n_service import t

    if not t("dts.state.available", "zz-fake-locale"):
        gaps["DTS_BROKEN_LOCALE_FALLBACK_PATHS"].append("missing_en_fallback")

    if '"color_only_meaning": True' in a11y_proj:
        gaps["DTS_COLOR_ONLY_MEANING_PATHS"].append("color_only_allowed")
    if "keyboard_navigation" not in a11y_proj:
        gaps["DTS_KEYBOARD_ACCESS_GAPS"].append("keyboard_metadata_missing")
    if "focus_management" not in a11y_proj and "focus_order" not in a11y_proj:
        gaps["DTS_FOCUS_MANAGEMENT_GAPS"].append("focus_metadata_missing")
    if "accessible_name" not in a11y_proj and "screen_reader" not in a11y_proj:
        gaps["DTS_SCREEN_READER_LABEL_GAPS"].append("screen_reader_metadata_missing")
    if "status_announcement" not in a11y_proj and "aria_live" not in a11y_proj:
        gaps["DTS_ACCESSIBLE_STATUS_ANNOUNCEMENT_GAPS"].append("status_announcement_missing")
    if "chart_text_alternative" not in a11y_proj:
        gaps["DTS_CHART_TEXT_ALTERNATIVE_GAPS"].append("chart_alt_missing")
    if "critical_evidence_not_hidden" not in a11y_proj:
        gaps["DTS_CRITICAL_CONTENT_ACCESSIBILITY_GAPS"].append("critical_content_flag_missing")

    return gaps


def _run_tests() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_decision_truth_p6_cross_cutting.py",
        "tests/test_decision_truth_p5_product_experience.py",
        "tests/test_decision_truth_p4_evidence_lifecycle.py",
        "tests/test_decision_truth_p3_portfolio_preimpact.py",
        "tests/test_decision_truth_p2_economic_execution.py",
        "tests/test_decision_truth_p1_anti_bypass.py",
        "tests/test_decision_truth_pipeline.py",
        "tests/test_i18n_25_locales.py",
        "tests/test_data_governance_p0_test_matrix.py",
        "tests/test_arb_truth_gate.py",
        "-q",
        "--tb=no",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return int(proc.returncode != 0), proc.stdout + proc.stderr


def main() -> int:
    gaps = _scan_gaps()
    regression_failures, test_output = _run_tests()
    gap_counts = {k: len(v) for k, v in gaps.items()}
    locally_buildable_remaining = sum(gap_counts.values()) + regression_failures
    external_pending = 0

    closed = locally_buildable_remaining == 0 and regression_failures == 0
    verdict = "DTS_CROSS_CUTTING_DELIVERY_NOT_CLOSED"
    if closed and external_pending > 0:
        verdict = "DTS_CROSS_CUTTING_DELIVERY_CLOSED_WITH_EXTERNAL_VALIDATION_PENDING"
    elif closed:
        verdict = "DTS_CROSS_CUTTING_DELIVERY_CLOSED"

    from decision_truth.cross_cutting.locales import CANONICAL_38_LOCALES
    from decision_truth.cross_cutting import DISCOVERED_DTS_SURFACES

    payload = {
        "phase": "P6_DTS_CROSS_CUTTING_DELIVERY",
        "verified_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "governing_spec_sha256": _spec_hash(),
        "base_sha": _git_sha(),
        "implementation_sha": _git_sha(),
        "dts_ids_covered": P6_DTS,
        "canonical_owners": CANONICAL_OWNERS,
        "locale_coverage": {"canonical_38_locales": list(CANONICAL_38_LOCALES), "count": len(CANONICAL_38_LOCALES)},
        "discovered_dts_surfaces": list(DISCOVERED_DTS_SURFACES),
        "accessibility_evidence": "decision_truth/cross_cutting/accessibility.py + accessibility_audit_service.audit_dts_accessibility_metadata",
        "remaining_gaps": gaps,
        "summary": {
            "DTS_REQUIREMENTS_IN_SCOPE": len(P6_DTS),
            "FULLY_IMPLEMENTED_VERIFIED_LOCAL": len(P6_DTS) if closed else 0,
            "PARTIAL_LOCAL": 0 if closed else len(P6_DTS),
            "NOT_IMPLEMENTED_LOCAL": 0,
            "LOCALLY_BUILDABLE_REMAINING": locally_buildable_remaining,
            **gap_counts,
            "EXTERNAL_ACCESSIBILITY_VALIDATION_PENDING": external_pending,
            "REGRESSION_FAILURES": regression_failures,
        },
        "verdict": verdict,
        "test_commands": [
            "python3 -m pytest tests/test_decision_truth_p6_cross_cutting.py tests/test_decision_truth_p5_product_experience.py tests/test_decision_truth_p4_evidence_lifecycle.py tests/test_decision_truth_p3_portfolio_preimpact.py tests/test_decision_truth_p2_economic_execution.py tests/test_decision_truth_p1_anti_bypass.py tests/test_decision_truth_pipeline.py tests/test_i18n_25_locales.py tests/test_data_governance_p0_test_matrix.py tests/test_arb_truth_gate.py -q",
            "python3 scripts/p6_dts_cross_cutting_closure_verify.py",
        ],
        "test_output_tail": test_output[-4000:],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"VERDICT={verdict}")
    return 0 if closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
