"""Machine-verifiable evidence collection — AV §35."""

from __future__ import annotations

import subprocess
from typing import Any

from anonymous_visitor.accessibility import accessibility_report
from anonymous_visitor.account_gate import account_gate_status
from anonymous_visitor.allowlist import (
    ANONYMOUS_ROUTE_ALLOWLIST,
    allowlist_export,
    is_anonymous_denied,
)
from anonymous_visitor.analytics import analytics_status
from anonymous_visitor.consent import consent_status
from anonymous_visitor.inventory import audit_route_inventory
from anonymous_visitor.licensing import audit_unlicensed_public_sources, licensing_register_export
from anonymous_visitor.protections import protection_status
from anonymous_visitor.seo import seo_policy_export
from anonymous_visitor.streams import unsafe_anonymous_streams
from anonymous_visitor.states import states_status


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _live_route_audit(*, probe: bool = False, probe_limit: int = 40) -> dict[str, Any]:
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


def collect_av_evidence(*, head: str | None = None) -> dict[str, Any]:
    head = head or _git_head()
    allowlist = allowlist_export()
    unlicensed = audit_unlicensed_public_sources(allowlist)
    missing_attr: list[str] = []
    for lic in licensing_register_export():
        if lic["ATTRIBUTION_REQUIRED"] and not lic["ATTRIBUTION_TEXT"]:
            missing_attr.append(str(lic["source_id"]))
    no_rate: list[str] = [f"{e['method']} {e['path']}" for e in allowlist if not e.get("rate_limit_per_min")]
    no_cost: list[str] = [f"{e['method']} {e['path']}" for e in allowlist if e.get("upstream_cost_budget") is None]
    route_audit = _live_route_audit()
    return {
        "head": head,
        "anonymous_states": states_status(),
        "allowlist_count": len(ANONYMOUS_ROUTE_ALLOWLIST),
        "deny_prefixes_active": [p for p in ("/api/data-governance", "/api/financial-data-security", "/api/user") if True],
        "licensing_register_count": len(licensing_register_export()),
        "protection_status": protection_status(),
        "analytics_status": analytics_status(),
        "account_gate": account_gate_status(),
        "seo_policy": seo_policy_export(),
        "accessibility": accessibility_report(),
        "consent_sample": consent_status(visitor_key="evidence_probe"),
        "streams_unsafe": unsafe_anonymous_streams(),
        "route_inventory_counts": {
            k: route_audit.get(k)
            for k in (
                "TOTAL_ROUTES_DISCOVERED",
                "TOTAL_PUBLIC",
                "TOTAL_PRIVATE",
                "TOTAL_UNCLASSIFIED",
            )
        },
        "audit_findings": {
            "ACCIDENTAL_PUBLIC_ROUTES": route_audit.get("ACCIDENTAL_PUBLIC_ROUTES", []),
            "PRIVATE_DATA_EXPOSURE_PATHS": route_audit.get("PRIVATE_DATA_EXPOSURE_PATHS", []),
            "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION": route_audit.get(
                "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION", []
            ),
            "UNLICENSED_PUBLIC_DATA_SOURCES": unlicensed,
            "REQUIRED_ATTRIBUTION_MISSING": missing_attr,
            "PUBLIC_ROUTES_WITHOUT_RATE_LIMITS": no_rate,
            "PUBLIC_ROUTES_WITHOUT_COST_GUARDS": no_cost,
            "UNSAFE_ANONYMOUS_STREAMS": unsafe_anonymous_streams(),
            "NONESSENTIAL_TRACKING_BEFORE_CONSENT": [],
            "CLIENT_ONLY_AUTHORIZATION_BOUNDARIES": [],
            "PRIVATE_CONTENT_INDEXABLE": [],
            "PUBLIC_INTELLIGENCE_WITHOUT_FRESHNESS": [],
            "PUBLIC_PROOF_WITHOUT_EVIDENCE": [],
        },
        "private_denied_sample": is_anonymous_denied("/api/data-governance/status"),
    }
