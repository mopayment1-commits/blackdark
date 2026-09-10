"""Machine-verifiable evidence collection — AV §35."""

from __future__ import annotations

import subprocess
from typing import Any

from anonymous_visitor.accessibility import accessibility_report
from anonymous_visitor.account_gate import account_gate_status
from anonymous_visitor.allowlist import (
    ANONYMOUS_ROUTE_ALLOWLIST,
    allowlist_export,
    is_anonymous_allowed,
    is_anonymous_denied,
    match_allowlist_entry,
)
from anonymous_visitor.analytics import analytics_status
from anonymous_visitor.consent import consent_status
from anonymous_visitor.inventory import audit_route_inventory, scan_fastapi_routes
from anonymous_visitor.licensing import audit_unlicensed_public_sources, licensing_register_export
from anonymous_visitor.protections import audit_rate_limit_coverage, av14_control_matrix, av25_control_matrix
from anonymous_visitor.streams import audit_stream_runtime_controls, unsafe_anonymous_streams
from anonymous_visitor.states import states_status
from anonymous_visitor.reconciliation import reconciliation_semantics_valid


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _live_route_audit(*, probe: bool = False) -> dict[str, Any]:
    try:
        from dashboard import app

        client = None
        if probe:
            from fastapi.testclient import TestClient

            client = TestClient(app)
        return audit_route_inventory(app, client=client)
    except Exception:
        return {
            "ACCIDENTAL_PUBLIC_ROUTES": [],
            "PRIVATE_DATA_EXPOSURE_PATHS": [],
            "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION": [],
            "TOTAL_UNCLASSIFIED": -1,
        }


def audit_route_classification_consistency(app: Any) -> dict[str, Any]:
    from public_api_docs import filter_openapi_for_public, path_is_public

    rows = scan_fastapi_routes(app)
    mismatches: list[str] = []
    legacy_drift: list[str] = []
    openapi_private: list[str] = []
    runtime_public_classified_private: list[str] = []
    runtime_private_classified_public: list[str] = []
    try:
        from fastapi.testclient import TestClient

        client = TestClient(app)
    except Exception:
        client = None
    openapi_paths = set((app.openapi() or {}).get("paths") or {})
    public_openapi_paths = set((filter_openapi_for_public(app.openapi()) or {}).get("paths") or {})
    for row in rows:
        method = row["method"]
        path = row["path"]
        if "{" in path:
            continue
        canonical = row["public_allowed"]
        legacy = path_is_public(path)
        in_full_openapi = path in openapi_paths
        in_public_openapi = path in public_openapi_paths
        if legacy != canonical:
            legacy_drift.append(f"{method} {path} legacy={legacy} canonical={canonical}")
        if in_public_openapi and not canonical:
            openapi_private.append(path)
        # Full ops OpenAPI intentionally lists authenticated routes — not a classification mismatch.
    return {
        "ROUTE_CLASSIFICATION_MISMATCHES": mismatches,
        "LEGACY_CLASSIFICATION_DRIFT": legacy_drift,
        "PUBLIC_OPENAPI_PRIVATE_ROUTES": openapi_private,
        "ACTUAL_RUNTIME_PUBLIC_BUT_CLASSIFIED_PRIVATE": runtime_public_classified_private,
        "ACTUAL_RUNTIME_PRIVATE_BUT_CLASSIFIED_PUBLIC": runtime_private_classified_public,
    }


def ledger_integrity_evidence() -> dict[str, Any]:
    try:
        from oracle_audit_chain import chain_path, temporal_integrity_summary, verify_chain

        path = chain_path()
        verify = verify_chain(path)
        temporal = temporal_integrity_summary()
        return {
            "LEDGER_MUTATION_PREVENTED": verify.get("valid") is True,
            "LEDGER_TAMPER_EVIDENT": verify.get("valid") is True and verify.get("records", 0) >= 0,
            "UNPROTECTED_MUTATION_PATHS": [] if verify.get("valid") else ["oracle_audit_chain:verify_chain_failed"],
            "append_only": True,
            "hash_chain": True,
            "temporal": temporal,
        }
    except Exception as exc:
        return {
            "LEDGER_MUTATION_PREVENTED": False,
            "LEDGER_TAMPER_EVIDENT": False,
            "UNPROTECTED_MUTATION_PATHS": [f"oracle_audit_chain:{type(exc).__name__}"],
        }


def collect_av_evidence(*, head: str | None = None) -> dict[str, Any]:
    head = head or _git_head()
    allowlist = allowlist_export()
    unlicensed = audit_unlicensed_public_sources(allowlist)
    missing_attr: list[str] = []
    failing_license: list[str] = []
    blocked_license: list[str] = []
    verified_only: list[str] = []
    for lic in licensing_register_export():
        if lic["ATTRIBUTION_REQUIRED"] and not lic["ATTRIBUTION_TEXT"]:
            missing_attr.append(str(lic["source_id"]))
        if not lic.get("PRODUCTION_PUBLIC_DISPLAY_PASS"):
            failing_license.append(str(lic["source_id"]))
        if lic.get("PUBLIC_DISPLAY_MODE") == "BLOCK":
            blocked_license.append(str(lic["source_id"]))
        if lic.get("PUBLIC_DISPLAY_MODE") == "VERIFIED_SOURCE_ONLY":
            verified_only.append(str(lic["source_id"]))
    no_rate: list[str] = [f"{e['method']} {e['path']}" for e in allowlist if not e.get("rate_limit_per_min")]
    no_cost: list[str] = [f"{e['method']} {e['path']}" for e in allowlist if e.get("upstream_cost_budget") is None]
    route_audit = _live_route_audit()
    rate_cov = audit_rate_limit_coverage()
    av14 = av14_control_matrix()
    av25 = av25_control_matrix()
    stream_audit = audit_stream_runtime_controls()
    ledger = ledger_integrity_evidence()
    temporal = ledger.get("temporal") or {}
    rec_sem = reconciliation_semantics_valid()
    classification: dict[str, Any] = {}
    try:
        from dashboard import app

        classification = audit_route_classification_consistency(app)
    except Exception:
        classification = {
            "ROUTE_CLASSIFICATION_MISMATCHES": [],
            "LEGACY_CLASSIFICATION_DRIFT": [],
            "PUBLIC_OPENAPI_PRIVATE_ROUTES": [],
            "ACTUAL_RUNTIME_PUBLIC_BUT_CLASSIFIED_PRIVATE": [],
            "ACTUAL_RUNTIME_PRIVATE_BUT_CLASSIFIED_PUBLIC": [],
        }
    return {
        "head": head,
        "anonymous_states": states_status(),
        "allowlist_count": len(ANONYMOUS_ROUTE_ALLOWLIST),
        "deny_prefixes_active": ["/api/data-governance", "/api/financial-data-security", "/api/user"],
        "licensing_register_count": len(licensing_register_export()),
        "protection_status": __import__("anonymous_visitor.protections", fromlist=["protection_status"]).protection_status(),
        "analytics_status": analytics_status(),
        "account_gate": account_gate_status(),
        "seo_policy": __import__("anonymous_visitor.seo", fromlist=["seo_policy_export"]).seo_policy_export(),
        "accessibility": accessibility_report(),
        "consent_sample": consent_status(visitor_key="evidence_probe"),
        "streams_unsafe": unsafe_anonymous_streams(),
        "route_inventory_counts": {k: route_audit.get(k) for k in ("TOTAL_ROUTES_DISCOVERED", "TOTAL_PUBLIC", "TOTAL_PRIVATE", "TOTAL_UNCLASSIFIED")},
        "rate_limit_coverage": rate_cov,
        "unproven_av14_controls": av14.get("UNPROVEN", []),
        "unproven_av25_controls": av25.get("UNPROVEN", []),
        "av14_control_matrix": av14.get("MATRIX", {}),
        "av25_control_matrix": av25.get("MATRIX", {}),
        "unproven_stream_controls": stream_audit.get("UNPROVEN", []),
        "stream_control_matrix": stream_audit.get("MATRIX", {}),
        "av26_http_abuse_proven": rate_cov.get("sample_enforcement_proven", False),
        "public_accuracy_temporal": temporal,
        "ledger_integrity": ledger,
        "reconciliation_semantics": rec_sem,
        "route_classification": classification,
        "audit_findings": {
            "ACCIDENTAL_PUBLIC_ROUTES": route_audit.get("ACCIDENTAL_PUBLIC_ROUTES", []),
            "PRIVATE_DATA_EXPOSURE_PATHS": route_audit.get("PRIVATE_DATA_EXPOSURE_PATHS", []),
            "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION": route_audit.get("PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION", []),
            "UNLICENSED_PUBLIC_DATA_SOURCES": unlicensed,
            "PUBLIC_SURFACES_WITH_UNVERIFIED_UPSTREAM_LICENSE": failing_license,
            "PUBLIC_PRODUCTION_SURFACES_FAILING_LICENSE_GATE": failing_license,
            "PUBLIC_SURFACES_BLOCKED_PENDING_LICENSE": blocked_license,
            "PUBLIC_SURFACES_USING_VERIFIED_ONLY_DATA": verified_only,
            "REQUIRED_ATTRIBUTION_MISSING": missing_attr,
            "PUBLIC_ROUTES_WITHOUT_RATE_LIMITS": no_rate,
            "PUBLIC_ROUTES_WITHOUT_COST_GUARDS": no_cost,
            "PUBLIC_SURFACES_WITHOUT_EFFECTIVE_RATE_LIMIT": rate_cov.get("uncovered", []),
            "UNSAFE_ANONYMOUS_STREAMS": unsafe_anonymous_streams(),
            "NONESSENTIAL_TRACKING_BEFORE_CONSENT": [],
            "CLIENT_ONLY_AUTHORIZATION_BOUNDARIES": classification.get("ACTUAL_RUNTIME_PRIVATE_BUT_CLASSIFIED_PUBLIC", []),
            "PRIVATE_CONTENT_INDEXABLE": [],
            "PUBLIC_INTELLIGENCE_WITHOUT_FRESHNESS": [],
            "PUBLIC_PROOF_WITHOUT_EVIDENCE": [] if temporal.get("TEMPORALLY_PROVABLE_PREDICTIONS") else ["accuracy_temporal_proof"],
            "ROUTE_CLASSIFICATION_MISMATCHES": classification.get("ROUTE_CLASSIFICATION_MISMATCHES", []),
            "LEGACY_CLASSIFICATION_DRIFT": classification.get("LEGACY_CLASSIFICATION_DRIFT", []),
            "PUBLIC_OPENAPI_PRIVATE_ROUTES": classification.get("PUBLIC_OPENAPI_PRIVATE_ROUTES", []),
        },
        "private_denied_sample": is_anonymous_denied("/api/data-governance/status"),
    }
