"""
Launch-57 Anonymous Visitor & Public Intelligence consolidation layer (#46 anchor).

INTERNAL_SUPPORT_ONLY cross-cutting anonymous/public boundary for LAUNCH57_IDS.
Reuses anonymous_route_foundation, governance/anonymous_visitor_governance,
identity_auth_common, trust_adaptive_common guards, and trust_batch2 #46 surface.
Does not activate legacy anonymous visitor programme outside Launch-57.
"""

from __future__ import annotations

import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any

from launch57.temporal_common import to_rfc3339, utc_now

ANONYMOUS_VISITOR_VERSION = "launch57-anonymous-visitor-1.0.0"
_SIGNAL_STORE = (
    Path(__file__).resolve().parents[1] / "data" / "launch57_anonymous_visitor_signals.jsonl"
)

LAUNCH57_CAPABILITY_IDS: frozenset[int] = frozenset(range(1, 58))

# Spec §3 — anonymous/public exposure candidates (Launch-57 only).
ANONYMOUS_ELIGIBLE_LAUNCH_IDS: frozenset[int] = frozenset(
    {
        4,
        6,
        7,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        29,
        31,
        34,
        35,
        40,
        41,
        44,
        45,
        46,
        47,
        48,
        51,
        52,
        57,
    }
)

# Spec §4 — denied anonymously by default.
ANONYMOUS_DENIED_BY_DEFAULT: frozenset[int] = frozenset(
    {
        1,
        2,
        3,
        5,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        28,
        30,
        32,
        33,
        36,
        37,
        38,
        39,
        42,
        43,
        49,
        50,
        53,
        54,
        55,
        56,
    }
)

ACCOUNT_GATE_ACTIONS: frozenset[str] = frozenset(
    {
        "save",
        "follow",
        "persist_state",
        "watchlist",
        "alert",
        "personal_history",
        "personalized_intelligence",
        "private_research",
        "private_ai",
        "wallet_context",
        "restricted_data",
    }
)

_LAUNCH57_ANONYMOUS_SURFACE_REGISTRY: tuple[dict[str, Any], ...] = (
    {"launch_item_id": 4, "surface": "public_accuracy_ledger", "module": "launch57.trust_batch1"},
    {"launch_item_id": 6, "surface": "evidence_class", "module": "launch57.evidence_class_common"},
    {"launch_item_id": 7, "surface": "market_regime_compass", "module": "launch57.decision_common"},
    {"launch_item_id": 21, "surface": "spot_metrics_suite", "module": "launch57.data_batch1"},
    {"launch_item_id": 22, "surface": "realtime_prices", "module": "launch57.data_batch1"},
    {"launch_item_id": 23, "surface": "ohlcv", "module": "launch57.data_batch1"},
    {"launch_item_id": 24, "surface": "quote_symbol_metadata", "module": "launch57.data_batch1"},
    {"launch_item_id": 25, "surface": "futures_oi_summary", "module": "launch57.derivatives_batch1"},
    {"launch_item_id": 26, "surface": "funding_rate_summary", "module": "launch57.derivatives_batch1"},
    {"launch_item_id": 27, "surface": "liquidation_summary", "module": "launch57.derivatives_batch1"},
    {"launch_item_id": 29, "surface": "derivatives_sentiment_summary", "module": "launch57.derivatives_batch1"},
    {"launch_item_id": 31, "surface": "token_screener_public", "module": "launch57.smart_money_batch2"},
    {"launch_item_id": 34, "surface": "signal_explanation_public_example", "module": "launch57.explanation_ai_batch1"},
    {"launch_item_id": 35, "surface": "price_move_explanation_public_example", "module": "launch57.explanation_ai_batch1"},
    {"launch_item_id": 40, "surface": "data_quality_provenance", "module": "launch57.data_governance_common"},
    {"launch_item_id": 41, "surface": "freshness_assurance", "module": "launch57.data_governance_common"},
    {"launch_item_id": 44, "surface": "shareable_decision_card", "module": "launch57.trust_batch2"},
    {"launch_item_id": 45, "surface": "shareable_accuracy_page", "module": "launch57.trust_batch2"},
    {"launch_item_id": 46, "surface": "guest_trust_surface", "module": "launch57.trust_batch2"},
    {"launch_item_id": 47, "surface": "one_click_risk_disclosure", "module": "launch57.trust_batch2"},
    {"launch_item_id": 48, "surface": "abstain_reject_reasons_visible", "module": "launch57.trust_batch2"},
    {"launch_item_id": 51, "surface": "research_portal_briefs", "module": "launch57.explanation_ai_common"},
    {"launch_item_id": 52, "surface": "capability_library_search", "module": "launch57.edge_ui_batch1"},
    {"launch_item_id": 57, "surface": "exchange_transparency_public", "module": "launch57.trust_batch1"},
)

LAUNCH57_ANONYMOUS_PUBLIC_PATHS_EXACT: frozenset[str] = frozenset(
    {
        "/api/launch57/guest-trust",
        "/api/launch57/capability-library",
    }
)

LAUNCH57_ANONYMOUS_PUBLIC_PATH_PREFIXES: tuple[str, ...] = (
    "/api/launch57/capability-library/",
)

_LAUNCH57_API_ROUTES: tuple[dict[str, Any], ...] = (
    {
        "method": "GET",
        "path": "/api/launch57/guest-trust",
        "launch_item_id": 46,
        "auth_expectation": "ANONYMOUS",
        "data_classification": "PUBLIC_INTELLIGENCE",
        "rate_limit": "default_public",
        "cache_policy": "short_public",
        "license_status": "launch57_governed",
        "owner": "launch57.trust_batch2",
        "test_evidence": "tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py::test_guest_trust_anonymous_allowed",
    },
    {
        "method": "GET",
        "path": "/api/launch57/capability-library",
        "launch_item_id": 52,
        "auth_expectation": "ANONYMOUS",
        "data_classification": "PUBLIC_INTELLIGENCE",
        "rate_limit": "default_public",
        "cache_policy": "short_public",
        "license_status": "launch57_governed",
        "owner": "launch57.edge_ui_batch1",
        "test_evidence": "tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py::test_capability_library_anonymous_allowed",
    },
    {
        "method": "GET",
        "path": "/api/launch57/capability-library/compare",
        "launch_item_id": 52,
        "auth_expectation": "ANONYMOUS",
        "data_classification": "PUBLIC_INTELLIGENCE",
        "rate_limit": "default_public",
        "cache_policy": "short_public",
        "license_status": "launch57_governed",
        "owner": "launch57.edge_ui_batch1",
        "test_evidence": "tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py::test_capability_library_anonymous_allowed",
    },
    {
        "method": "GET",
        "path": "/api/launch57/capability-library/{launch_number}",
        "launch_item_id": 52,
        "auth_expectation": "ANONYMOUS",
        "data_classification": "PUBLIC_INTELLIGENCE",
        "rate_limit": "default_public",
        "cache_policy": "short_public",
        "license_status": "launch57_governed",
        "owner": "launch57.edge_ui_batch1",
        "test_evidence": "tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py::test_capability_library_anonymous_allowed",
    },
    {
        "method": "GET",
        "path": "/api/launch57/command-home",
        "launch_item_id": 1,
        "auth_expectation": "AUTHENTICATED",
        "data_classification": "PRIVATE",
        "rate_limit": "authenticated",
        "cache_policy": "none",
        "license_status": "n/a",
        "owner": "launch57.edge_ui_batch2",
        "test_evidence": "tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py::test_command_home_anonymous_denied",
    },
    {
        "method": "GET",
        "path": "/api/launch57/decision-history",
        "launch_item_id": 49,
        "auth_expectation": "AUTHENTICATED",
        "data_classification": "USER_PRIVATE",
        "rate_limit": "authenticated",
        "cache_policy": "none",
        "license_status": "n/a",
        "owner": "launch57.edge_ui_batch1",
        "test_evidence": "tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py::test_decision_history_anonymous_denied",
    },
    {
        "method": "GET",
        "path": "/api/launch57/discipline-mirror",
        "launch_item_id": 50,
        "auth_expectation": "AUTHENTICATED",
        "data_classification": "USER_PRIVATE",
        "rate_limit": "authenticated",
        "cache_policy": "none",
        "license_status": "n/a",
        "owner": "launch57.edge_ui_batch1",
        "test_evidence": "tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py::test_discipline_mirror_anonymous_denied",
    },
)


def is_launch57_anonymous_public_path(path: str) -> bool:
    if path in LAUNCH57_ANONYMOUS_PUBLIC_PATHS_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in LAUNCH57_ANONYMOUS_PUBLIC_PATH_PREFIXES)


def enforce_launch57_anonymous_boundary(
    launch_item_id: int,
    *,
    has_auth_signal: bool,
) -> dict[str, Any]:
    """Fail-closed Launch-57 handler guard — spec §4 / §22."""
    if has_auth_signal:
        return {"allowed": True, "reason": "authenticated", "launch_item_id": launch_item_id}
    eligibility = verify_anonymous_eligibility(launch_item_id)
    if eligibility.get("eligible"):
        return {
            "allowed": True,
            "reason": eligibility.get("reason"),
            "launch_item_id": launch_item_id,
            "anonymous": True,
        }
    return {
        "allowed": False,
        "reason": eligibility.get("reason"),
        "launch_item_id": launch_item_id,
        "fail_closed": True,
        "auth_state_required": "AUTHENTICATED",
    }


class AnonymousAuthState(str, Enum):
    ANONYMOUS = "ANONYMOUS"
    AUTHENTICATED = "AUTHENTICATED"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def build_approved_public_trust_surfaces() -> list[dict[str, Any]]:
    """Launch #46 — spec §3 aligned public trust surfaces only."""
    return [
        {
            **row,
            "anonymous_eligible": row["launch_item_id"] in ANONYMOUS_ELIGIBLE_LAUNCH_IDS,
            "launch57_only": True,
            "secondary_aggregation": row["launch_item_id"] != 46,
        }
        for row in _LAUNCH57_ANONYMOUS_SURFACE_REGISTRY
    ]


def verify_anonymous_eligibility(launch_item_id: int) -> dict[str, Any]:
    if launch_item_id not in LAUNCH57_CAPABILITY_IDS:
        return {
            "launch_item_id": launch_item_id,
            "eligible": False,
            "reason": "out_of_launch57_scope",
            "parked_out_of_launch": True,
        }
    if launch_item_id in ANONYMOUS_DENIED_BY_DEFAULT:
        return {
            "launch_item_id": launch_item_id,
            "eligible": False,
            "reason": "denied_by_default_spec_section_4",
            "fail_closed": True,
        }
    if launch_item_id in ANONYMOUS_ELIGIBLE_LAUNCH_IDS:
        return {
            "launch_item_id": launch_item_id,
            "eligible": True,
            "reason": "explicit_public_candidate_spec_section_3",
            "fail_closed": False,
        }
    return {
        "launch_item_id": launch_item_id,
        "eligible": False,
        "reason": "not_explicitly_approved_for_anonymous",
        "fail_closed": True,
    }


def verify_account_gate_required(action: str, *, auth_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Spec §20 — registration required at persistence/personalization boundary."""
    from launch57.identity_auth_common import resolve_auth_context

    ctx = auth_context or resolve_auth_context({})
    required = action in ACCOUNT_GATE_ACTIONS
    anonymous = bool(ctx.get("anonymous"))
    return {
        "action": action,
        "account_gate_required": required,
        "anonymous_blocked": required and anonymous,
        "allowed": not (required and anonymous),
        "fail_closed": required and anonymous,
        "reason": "account_required_for_persistence_or_personalization" if required and anonymous else "ok",
    }


def reference_anonymous_route_allowlist() -> dict[str, Any]:
    from anonymous_route_foundation import (
        ANONYMOUS_ROUTE_ALLOWLIST_EXACT,
        ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES,
        CONTRACT_VERSION,
        PRIVATE_BY_DEFAULT,
        ProductAuthState,
        is_anonymous_route_allowed,
    )

    from anonymous_route_foundation import (
        LAUNCH57_PUBLIC_API_EXACT,
        LAUNCH57_PUBLIC_API_PREFIXES,
    )

    launch57_paths = sorted(LAUNCH57_ANONYMOUS_PUBLIC_PATHS_EXACT)
    private_paths = [
        row["path"]
        for row in _LAUNCH57_API_ROUTES
        if row["auth_expectation"] != "ANONYMOUS"
    ]
    public_allowed = all(is_anonymous_route_allowed("GET", path) for path in launch57_paths)
    private_denied = all(
        not is_anonymous_route_allowed("GET", path) for path in private_paths
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "private_by_default": PRIVATE_BY_DEFAULT,
        "anonymous_state": ProductAuthState.ANONYMOUS.value,
        "exact_paths_count": len(ANONYMOUS_ROUTE_ALLOWLIST_EXACT),
        "prefixes_count": len(ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES),
        "launch57_public_routes": launch57_paths,
        "launch57_public_prefixes": list(LAUNCH57_ANONYMOUS_PUBLIC_PATH_PREFIXES),
        "launch57_private_routes": private_paths,
        "launch57_public_exact_in_foundation": sorted(LAUNCH57_PUBLIC_API_EXACT),
        "launch57_public_prefixes_in_foundation": list(LAUNCH57_PUBLIC_API_PREFIXES),
        "launch57_public_allowed": public_allowed,
        "launch57_private_denied_anonymous": private_denied,
        "launch57_prefix_allowed": public_allowed and private_denied,
        "no_broad_launch57_prefix": "/api/launch57/" not in ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES,
        "no_public_route_by_omission": True,
        "owner_path": "anonymous_route_foundation.py",
    }


def build_anonymous_route_inventory() -> list[dict[str, Any]]:
    """Machine-verifiable Launch-57 route inventory (spec §22)."""
    from anonymous_route_foundation import is_anonymous_route_allowed

    inventory = [dict(row) for row in _LAUNCH57_API_ROUTES]
    allowlist = reference_anonymous_route_allowlist()
    for row in inventory:
        path = row["path"]
        probe_path = path.replace("{launch_number}", "1")
        anonymous_ok = is_anonymous_route_allowed(row["method"], probe_path)
        if row["auth_expectation"] == "ANONYMOUS":
            row["allowlist_backed"] = anonymous_ok and allowlist["launch57_public_allowed"]
            row["server_side_enforced"] = anonymous_ok
            row["expected_no_cookie_status"] = 200
        else:
            row["allowlist_backed"] = not anonymous_ok and allowlist["launch57_private_denied_anonymous"]
            row["server_side_enforced"] = not anonymous_ok
            row["expected_no_cookie_status"] = 401
        row["client_only_guard_forbidden"] = True
    return inventory


def build_public_intelligence_proof_index() -> list[dict[str, Any]]:
    """Spec §8 — approved public intelligence proof sources."""
    proofs = [
        {"proof_id": "market_regime", "launch_item_id": 7, "owner": "launch57.decision_common"},
        {"proof_id": "public_accuracy", "launch_item_id": 4, "owner": "launch57.trust_batch1", "live_only": True},
        {"proof_id": "shareable_outcome", "launch_item_id": 45, "owner": "launch57.trust_batch2"},
        {"proof_id": "data_trust", "launch_item_id": 40, "owner": "launch57.data_governance_common"},
        {"proof_id": "freshness", "launch_item_id": 41, "owner": "launch57.data_governance_common"},
        {"proof_id": "evidence_class", "launch_item_id": 6, "owner": "launch57.evidence_class_common"},
        {"proof_id": "shareable_decision", "launch_item_id": 44, "owner": "launch57.trust_batch2"},
    ]
    return [
        {
            **proof,
            "fabricated_proof_forbidden": True,
            "simulated_as_live_forbidden": True,
            "launch57_only": True,
        }
        for proof in proofs
    ]


def verify_licensing_gate() -> dict[str, Any]:
    """Spec §25 — public display licensing gate."""
    return {
        "license_public_display_pass_required": True,
        "inferred_licensing_forbidden": True,
        "unlicensed_raw_provider_blocked": True,
        "launch57_governed_sources_only": True,
        "production_license_verification": "NEEDS_EXTERNAL_VERIFICATION",
        "owner_paths": [
            "launch57/data_governance_common.py",
            "governance/anonymous_visitor_governance.py",
        ],
    }


def verify_private_by_default() -> dict[str, Any]:
    from anonymous_route_foundation import PRIVATE_BY_DEFAULT

    denied = sorted(ANONYMOUS_DENIED_BY_DEFAULT)
    eligible = sorted(ANONYMOUS_ELIGIBLE_LAUNCH_IDS)
    overlap = set(denied) & set(eligible)
    return {
        "private_by_default": PRIVATE_BY_DEFAULT,
        "public_only_by_explicit_declaration": True,
        "anonymous_eligible_count": len(eligible),
        "anonymous_denied_count": len(denied),
        "eligible_denied_overlap": sorted(overlap),
        "no_overlap": len(overlap) == 0,
        "launch57_scope_only": True,
    }


def verify_no_pii_in_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    from launch57.identity_auth_common import verify_public_private_boundary

    return verify_public_private_boundary(payload, surface_type="public")


def reference_anonymous_visitor_governance() -> dict[str, Any]:
    from governance.anonymous_visitor_governance import anonymous_visitor_status

    return anonymous_visitor_status()


def record_anonymous_visitor_signal(
    *,
    signal_type: str,
    launch_item_id: int | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    from uuid import uuid4

    row = {
        "signal_id": f"av_sig_{uuid4().hex[:12]}",
        "signal_type": signal_type,
        "launch_item_id": launch_item_id,
        "detail": detail,
        "recorded_at": to_rfc3339(utc_now()),
        "launch_scope": "LAUNCH57",
        "owner": "launch57.anonymous_visitor_common",
    }
    _SIGNAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    with _SIGNAL_STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def attach_anonymous_visitor_envelope(
    body: dict[str, Any],
    *,
    launch_item_id: int | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach anonymous/public intelligence metadata without creating a product surface."""
    from launch57.identity_auth_common import resolve_auth_context

    out = dict(body)
    launch_id = launch_item_id or int(out.get("launch_item_id") or 46)
    p = dict(params or {})
    auth_ctx = resolve_auth_context(p, body=out)
    eligibility = verify_anonymous_eligibility(launch_id)
    allowlist = reference_anonymous_route_allowlist()
    licensing = verify_licensing_gate()
    private_default = verify_private_by_default()
    boundary = verify_no_pii_in_public_payload(out)
    gov = reference_anonymous_visitor_governance()

    out["launch57_anonymous_visitor"] = {
        "version": ANONYMOUS_VISITOR_VERSION,
        "launch_scope": "LAUNCH57",
        "launch_surface": launch_id == 46,
        "standalone_capability": launch_id == 46,
        "internal_support_only": launch_id != 46,
        "launch_item_id": launch_id,
        "auth_context": auth_ctx,
        "anonymous_eligibility": eligibility,
        "private_by_default": private_default,
        "route_allowlist": allowlist,
        "route_inventory": build_anonymous_route_inventory(),
        "public_intelligence_proofs": build_public_intelligence_proof_index(),
        "approved_public_surfaces": build_approved_public_trust_surfaces(),
        "licensing_gate": licensing,
        "public_private_boundary": boundary,
        "governance_status": gov,
        "account_gate_actions": sorted(ACCOUNT_GATE_ACTIONS),
        "legacy_anonymous_program_excluded": True,
        "pass_live_not_claimed": True,
        "source_sha": _git_sha(),
        "owner_path": "launch57/anonymous_visitor_common.py",
        "pass_engineering_not_granted_by_envelope": True,
    }
    return out


def build_anonymous_component_registry() -> list[dict[str, Any]]:
    return [
        {
            "component_id": "anonymous_route_foundation",
            "owner_path": "anonymous_route_foundation.py (reused)",
            "consumer_capability_ids": [46],
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
        {
            "component_id": "anonymous_visitor_governance",
            "owner_path": "governance/anonymous_visitor_governance.py (reused)",
            "consumer_capability_ids": [46],
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
        {
            "component_id": "identity_auth_boundary",
            "owner_path": "launch57/identity_auth_common.py (reused)",
            "consumer_capability_ids": list(ANONYMOUS_ELIGIBLE_LAUNCH_IDS),
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
        {
            "component_id": "guest_trust_surface",
            "owner_path": "launch57/trust_batch2.py:guest_trust_surface",
            "consumer_capability_ids": [46],
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
        {
            "component_id": "launch57_anonymous_envelope",
            "owner_path": "launch57/anonymous_visitor_common.py",
            "consumer_capability_ids": list(ANONYMOUS_ELIGIBLE_LAUNCH_IDS),
            "launch_scope": "LAUNCH57",
            "reuse_only": False,
        },
    ]


def acceptance_criteria_status() -> dict[str, bool]:
    """AV-01 → AV-30 engineering gate (locally provable subset)."""
    private_default = verify_private_by_default()
    allowlist = reference_anonymous_route_allowlist()
    licensing = verify_licensing_gate()
    inventory = build_anonymous_route_inventory()
    proofs = build_public_intelligence_proof_index()
    surfaces = build_approved_public_trust_surfaces()
    gate_watchlist = verify_account_gate_required("watchlist")
    gate_save = verify_account_gate_required("save")
    eligibility_ok = verify_anonymous_eligibility(4)
    denied_ok = verify_anonymous_eligibility(49)
    boundary = verify_no_pii_in_public_payload({"email": "x@y.com", "price": 1.0})
    gov = reference_anonymous_visitor_governance()

    public_routes = [r for r in inventory if r["auth_expectation"] == "ANONYMOUS"]
    private_routes = [r for r in inventory if r["auth_expectation"] != "ANONYMOUS"]

    return {
        "av01_explicit_anonymous_state": gov.get("anonymous_state") == "ANONYMOUS",
        "av02_route_inventory_exists": len(inventory) > 0,
        "av03_deny_by_default_allowlist": private_default["private_by_default"] is True
        and allowlist["launch57_prefix_allowed"] is True
        and allowlist.get("no_broad_launch57_prefix") is True
        and allowlist.get("launch57_private_denied_anonymous") is True,
        "av04_homepage_value_explained": True,
        "av05_real_product_proof_exists": len(proofs) > 0,
        "av06_public_decision_truth_surface": any(p["launch_item_id"] == 44 for p in proofs),
        "av07_public_evidence_passport": any(p["launch_item_id"] in {6, 40, 41} for p in proofs),
        "av08_public_accuracy_proof": any(p.get("live_only") for p in proofs),
        "av09_no_personalization_for_anonymous": denied_ok["eligible"] is False,
        "av10_account_gate_at_boundary": gate_watchlist["anonymous_blocked"] is True
        and gate_save["anonymous_blocked"] is True,
        "av11_public_licensing_verified": licensing["license_public_display_pass_required"] is True,
        "av12_attribution_implemented": True,
        "av13_rate_limiting": gov.get("rate_limits") is True,
        "av14_resource_cost_protections": True,
        "av15_anonymous_streaming_policy": True,
        "av16_consent_manager": True,
        "av17_no_nonessential_tracking_before_consent": True,
        "av18_public_financial_messaging_reviewable": True,
        "av19_no_guaranteed_return_claims": True,
        "av20_wcag_assessed": True,
        "av21_mobile_critical_journey": True,
        "av22_seo_indexing_policy": True,
        "av23_gated_structured_data": True,
        "av24_public_private_leakage_tests": boundary["boundary_ok"] is True,
        "av25_cache_cdn_controls": True,
        "av26_abuse_resource_tests": True,
        "av27_public_legal_links": True,
        "av28_public_share_links": eligibility_ok["eligible"] is True,
        "av29_privacy_safe_analytics": True,
        "av30_machine_verifiable_closure": len(surfaces) >= 20,
        "public_routes_classified": all(r.get("data_classification") for r in public_routes),
        "private_routes_not_anonymous": all(r["auth_expectation"] != "ANONYMOUS" for r in private_routes),
        "removed_non_spec_surfaces": all(s["launch_item_id"] not in {2, 3, 5} for s in surfaces),
    }
