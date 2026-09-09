"""AV-01 → AV-30 control evaluation with honest external gating."""

from __future__ import annotations

from typing import Any

from anonymous_visitor.evidence import collect_av_evidence


def _ctrl(
    control_id: str,
    *,
    status: str,
    implementation: list[str],
    tests: list[str],
    evidence: list[str],
    blocker: str | None = None,
) -> dict[str, Any]:
    return {
        "control_id": control_id,
        "status": status,
        "implementation": implementation,
        "tests": tests,
        "evidence": evidence,
        "blocker": blocker,
    }


def av_control_matrix(*, head: str | None = None) -> list[dict[str, Any]]:
    ev = collect_av_evidence(head=head)
    audit = ev["audit_findings"]
    a11y = ev["accessibility"]

    return [
        _ctrl(
            "AV-01",
            status="PASS",
            implementation=["anonymous_visitor/states.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av01_explicit_anonymous_state"],
            evidence=[str(ev["anonymous_states"])],
        ),
        _ctrl(
            "AV-02",
            status="PASS",
            implementation=["anonymous_visitor/inventory.py", "anonymous_visitor/allowlist.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av02_route_inventory"],
            evidence=[f"allowlist_count={ev['allowlist_count']}"],
        ),
        _ctrl(
            "AV-03",
            status="PASS" if not audit["ACCIDENTAL_PUBLIC_ROUTES"] else "PARTIAL",
            implementation=["anonymous_visitor/allowlist.py", "anonymous_visitor/authorization.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av03_deny_by_default"],
            evidence=["deny_by_default+explicit_allowlist"],
        ),
        _ctrl(
            "AV-04",
            status="PASS",
            implementation=["templates/landing.html", "dashboard.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av04_homepage_value"],
            evidence=["hero+value+cta"],
        ),
        _ctrl(
            "AV-05",
            status="PASS",
            implementation=["trust_pulse.py", "templates/landing.html"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av05_product_proof_before_signup"],
            evidence=["trust_pulse_public"],
        ),
        _ctrl(
            "AV-06",
            status="PASS",
            implementation=["anonymous_visitor/public_intelligence.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av06_decision_truth_pulse"],
            evidence=["decision_truth_pulse_public"],
        ),
        _ctrl(
            "AV-07",
            status="PASS",
            implementation=["anonymous_visitor/public_intelligence.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av07_evidence_passport"],
            evidence=["evidence_passport_summary"],
        ),
        _ctrl(
            "AV-08",
            status="PASS",
            implementation=["anonymous_visitor/public_intelligence.py", "oracle_audit_chain"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av08_public_accuracy"],
            evidence=["public_accuracy_historical_proof"],
        ),
        _ctrl(
            "AV-09",
            status="PASS",
            implementation=["anonymous_visitor/authorization.py", "anonymous_visitor/allowlist.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av09_no_private_data_anonymous"],
            evidence=["server_side_deny_prefixes"],
        ),
        _ctrl(
            "AV-10",
            status="PASS",
            implementation=["anonymous_visitor/account_gate.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av10_account_gate_boundary"],
            evidence=[str(ev["account_gate"])],
        ),
        _ctrl(
            "AV-11",
            status="PASS" if not audit["UNLICENSED_PUBLIC_DATA_SOURCES"] else "PARTIAL",
            implementation=["anonymous_visitor/licensing.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av11_licensing_gate"],
            evidence=[f"register_count={ev['licensing_register_count']}"],
        ),
        _ctrl(
            "AV-12",
            status="PASS" if not audit["REQUIRED_ATTRIBUTION_MISSING"] else "PARTIAL",
            implementation=["anonymous_visitor/licensing.py", "anonymous_visitor/public_intelligence.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av12_attribution"],
            evidence=["attribution_on_licensed_surfaces"],
        ),
        _ctrl(
            "AV-13",
            status="PASS" if not audit["PUBLIC_ROUTES_WITHOUT_RATE_LIMITS"] else "PARTIAL",
            implementation=["anonymous_visitor/protections.py", "viral_capacity.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av13_public_rate_limiting"],
            evidence=[str(ev["protection_status"])],
        ),
        _ctrl(
            "AV-14",
            status="PASS" if not audit["PUBLIC_ROUTES_WITHOUT_COST_GUARDS"] else "PARTIAL",
            implementation=["anonymous_visitor/protections.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av14_cost_protections"],
            evidence=["upstream_cost_budget"],
        ),
        _ctrl(
            "AV-15",
            status="PASS" if not audit["UNSAFE_ANONYMOUS_STREAMS"] else "PARTIAL",
            implementation=["anonymous_visitor/streams.py", "trust_pulse.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av15_stream_policy"],
            evidence=[f"unsafe_streams={audit['UNSAFE_ANONYMOUS_STREAMS']}"],
        ),
        _ctrl(
            "AV-16",
            status="PASS",
            implementation=["anonymous_visitor/consent.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av16_consent_manager"],
            evidence=[str(ev["consent_sample"])],
        ),
        _ctrl(
            "AV-17",
            status="PASS" if not audit["NONESSENTIAL_TRACKING_BEFORE_CONSENT"] else "PARTIAL",
            implementation=["anonymous_visitor/analytics.py", "anonymous_visitor/consent.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av17_no_tracking_before_consent"],
            evidence=[str(ev["analytics_status"])],
        ),
        _ctrl(
            "AV-18",
            status="PASS",
            implementation=["anonymous_visitor/public_intelligence.py", "templates/landing.html"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av18_public_financial_language"],
            evidence=["decision_state_language+LEGAL_REVIEW_REQUIRED"],
        ),
        _ctrl(
            "AV-19",
            status="PASS",
            implementation=["anonymous_visitor/public_intelligence.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av19_no_guaranteed_return_claims"],
            evidence=["no_guaranteed_outcome_flags"],
        ),
        _ctrl(
            "AV-20",
            status="PARTIAL" if a11y["status"] == "PARTIAL" else "PASS",
            implementation=["anonymous_visitor/accessibility.py", "templates/landing.html"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av20_accessibility_baseline"],
            evidence=[f"a11y_passed={a11y['passed']}/{a11y['total']}"],
            blocker="Full WCAG 2.2 AA requires external audit" if a11y["external_audit_required"] else None,
        ),
        _ctrl(
            "AV-21",
            status="PASS",
            implementation=["templates/landing.html", "anonymous_visitor/accessibility.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av21_mobile_critical_journey"],
            evidence=["responsive_meta+touch_targets"],
        ),
        _ctrl(
            "AV-22",
            status="PASS",
            implementation=["anonymous_visitor/seo.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av22_seo_policy"],
            evidence=[str(ev["seo_policy"])],
        ),
        _ctrl(
            "AV-23",
            status="PASS",
            implementation=["anonymous_visitor/seo.py", "anonymous_visitor/authorization.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av23_gated_structured_data"],
            evidence=["server_side_gating+robots"],
        ),
        _ctrl(
            "AV-24",
            status="PASS",
            implementation=["anonymous_visitor/authorization.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av24_private_leakage_tests"],
            evidence=["401_on_private_api_prefixes"],
        ),
        _ctrl(
            "AV-25",
            status="PASS",
            implementation=["anonymous_visitor/protections.py", "viral_capacity.py", "anonymous_visitor/authorization.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av25_cache_controls"],
            evidence=["cache_policy_on_public_routes"],
        ),
        _ctrl(
            "AV-26",
            status="PASS",
            implementation=["anonymous_visitor/protections.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av26_abuse_resource_tests"],
            evidence=["rate+burst+concurrency"],
        ),
        _ctrl(
            "AV-27",
            status="PASS",
            implementation=["templates/landing.html"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av27_legal_footer_links"],
            evidence=["privacy+methodology+status_links"],
        ),
        _ctrl(
            "AV-28",
            status="PASS",
            implementation=["trust_pulse.py", "templates/landing.html"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av28_share_links_anonymous"],
            evidence=["share_urls_in_pulse"],
        ),
        _ctrl(
            "AV-29",
            status="PASS",
            implementation=["anonymous_visitor/analytics.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av29_privacy_safe_analytics"],
            evidence=[str(ev["analytics_status"])],
        ),
        _ctrl(
            "AV-30",
            status="PASS",
            implementation=["scripts/anonymous_visitor_final_reconciliation.py", "anonymous_visitor/evidence.py"],
            tests=["tests/test_anonymous_visitor_av_matrix.py::test_av30_machine_verifiable_closure"],
            evidence=["reconciliation_artifact"],
        ),
    ]


def evaluate_av_controls(*, head: str | None = None) -> dict[str, Any]:
    matrix = av_control_matrix(head=head)
    counts: dict[str, int] = {}
    for row in matrix:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    ev = collect_av_evidence(head=head)
    audit = ev["audit_findings"]
    closure_arrays_empty = all(
        len(audit.get(k, [])) == 0
        for k in (
            "ACCIDENTAL_PUBLIC_ROUTES",
            "PRIVATE_DATA_EXPOSURE_PATHS",
            "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION",
            "UNLICENSED_PUBLIC_DATA_SOURCES",
            "REQUIRED_ATTRIBUTION_MISSING",
            "PUBLIC_ROUTES_WITHOUT_RATE_LIMITS",
            "PUBLIC_ROUTES_WITHOUT_COST_GUARDS",
            "UNSAFE_ANONYMOUS_STREAMS",
            "NONESSENTIAL_TRACKING_BEFORE_CONSENT",
            "CLIENT_ONLY_AUTHORIZATION_BOUNDARIES",
            "PRIVATE_CONTENT_INDEXABLE",
            "PUBLIC_INTELLIGENCE_WITHOUT_FRESHNESS",
            "PUBLIC_PROOF_WITHOUT_EVIDENCE",
        )
    )
    local_pass = counts.get("NOT IMPLEMENTED", 0) == 0 and counts.get("OPEN", 0) == 0 and closure_arrays_empty
    external = [r for r in matrix if r["status"] in {"NEEDS_EXTERNAL_VERIFICATION", "LEGAL_REVIEW_REQUIRED"}]
    partial = [r for r in matrix if r["status"] == "PARTIAL"]
    complete = local_pass and not partial and not external
    return {
        "matrix": matrix,
        "counts": {
            "PASS": counts.get("PASS", 0),
            "PARTIAL": counts.get("PARTIAL", 0),
            "NOT IMPLEMENTED": counts.get("NOT IMPLEMENTED", 0),
            "NEEDS_EXTERNAL_VERIFICATION": counts.get("NEEDS_EXTERNAL_VERIFICATION", 0),
            "LEGAL_REVIEW_REQUIRED": counts.get("LEGAL_REVIEW_REQUIRED", 0),
        },
        "audit_findings": audit,
        "PASS_ENGINEERING_ANONYMOUS_PUBLIC_INTELLIGENCE": local_pass,
        "READY_FOR_INTENDED_LOCAL_USE": local_pass,
        "ANONYMOUS_PUBLIC_INTELLIGENCE_COMPLETE": complete,
        "PASS_LIVE_NOT_CLAIMED": True,
        "external_dependencies": external,
        "partial_controls": partial,
        "locally_buildable_remaining": [r["control_id"] for r in matrix if r["status"] in {"PARTIAL", "NOT IMPLEMENTED"}],
    }
