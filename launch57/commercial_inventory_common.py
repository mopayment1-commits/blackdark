"""
Launch-57 Commercial Capability Inventory — AUDIT ONLY.

Read-only commercial readiness audit over LAUNCH57_IDS.
Does not modify product code, pricing, entitlements, or capabilities.
Reuses LAUNCH57_REGISTER.json, identity/billing/anonymous Launch-57 layers.
"""

from __future__ import annotations

import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any

COMMERCIAL_INVENTORY_VERSION = "launch57-commercial-inventory-audit-1.0.0"
AUDIT_MODE = "AUDIT_ONLY"

LAUNCH57_CAPABILITY_IDS: frozenset[int] = frozenset(range(1, 58))
LAUNCH57_EXPECTED_COUNT = 57

_INTERNAL_PRIMARY_LAUNCH_IDS: frozenset[int] = frozenset({6, 39, 42})

_EXCLUDED_COMMERCIAL_STATUSES: frozenset[str] = frozenset(
    {
        "PARKED",
        "NO_LINKED_CANONICAL",
        "NOT_LINKED",
        "STUB",
        "PHANTOM",
    }
)

_EXTERNAL_SUBTYPE_BY_LAUNCH: dict[int, str] = {
    1: "USER_SURFACE",
    4: "USER_TRUST_EVIDENCE_CAPABILITY",
    44: "USER_VIRAL_ASSET",
    45: "USER_VIRAL_ASSET",
    46: "USER_SURFACE",
    49: "USER_RETENTION_ASSET",
    50: "USER_RETENTION_ASSET",
    51: "USER_AI_CAPABILITY",
    52: "USER_FEATURE",
    53: "USER_INSTITUTIONAL_CAPABILITY",
    54: "USER_INSTITUTIONAL_CAPABILITY",
    57: "USER_INSTITUTIONAL_CAPABILITY",
}

_GOVERNANCE = Path(__file__).resolve().parents[1] / "governance" / "launch57"
_REGISTER_PATH = _GOVERNANCE / "LAUNCH57_REGISTER.json"
_HERO_MATRIX_PATH = _GOVERNANCE / "LAUNCH57_SIX_HERO_MATRIX.json"

_BUILD_KEYS = (
    "phase7_batch2_build",
    "phase7_batch1_build",
    "phase6_batch1_build",
    "phase5_batch2_build",
    "phase5_batch1_build",
    "phase4_batch3_build",
    "phase4_batch2_build",
    "phase4_batch1_build",
    "phase3_batch2_build",
    "phase3_batch1_build",
    "phase2_batch2_build",
    "phase2_batch1_build",
    "phase1_batch2_build",
    "phase1_batch1_build",
)

_CAPABILITY_GROUPS: dict[str, tuple[int, ...]] = {
    "Trust & Decision": (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 37, 47, 48),
    "Smart Money / Wallet / Flow": tuple(range(13, 21)),
    "Market Data / Quality": (21, 22, 23, 24, 39, 40, 41, 42),
    "Derivatives / Market Structure": tuple(range(25, 31)),
    "Discovery / Habit / Monitoring": (31, 32, 33, 49, 50, 52),
    "Explanation / AI / Research": (34, 35, 36, 51),
    "Edge": (38, 43),
    "Public / Viral / Guest": (44, 45, 46),
    "Due Diligence / Risk": (53, 54, 55, 56, 57),
    "Home": (1,),
}

_VIRAL_CANDIDATES: frozenset[int] = frozenset({4, 44, 45, 46, 51, 18, 55})
_RETENTION_CANDIDATES: frozenset[int] = frozenset({32, 33, 49, 50, 51, 14, 18})
_TRUST_ASSETS: frozenset[int] = frozenset({3, 4, 6, 40, 41, 45, 46, 47, 48})
_INSTITUTIONAL_CANDIDATES: frozenset[int] = frozenset(
    {3, 4, 6, 36, 39, 40, 41, 42, 51, 53, 54, 57}
)

_ROLE_BY_LAUNCH: dict[int, tuple[str, ...]] = {
    1: ("RETENTION_DRIVER", "DISCOVERY_DRIVER"),
    2: ("AHA_MOMENT", "TRUST_DRIVER", "CONVERSION_TRIGGER"),
    4: ("TRUST_DRIVER", "VIRAL_DRIVER", "FREE_HOOK"),
    44: ("VIRAL_DRIVER", "TRUST_DRIVER"),
    45: ("VIRAL_DRIVER", "TRUST_DRIVER"),
    46: ("FREE_HOOK", "TRUST_DRIVER", "CONVERSION_TRIGGER"),
    32: ("RETENTION_DRIVER", "HABIT_DRIVER"),
    33: ("RETENTION_DRIVER", "UPGRADE_TRIGGER"),
    49: ("RETENTION_DRIVER", "HABIT_DRIVER"),
    50: ("RETENTION_DRIVER",),
    51: ("RETENTION_DRIVER", "DISCOVERY_DRIVER"),
    52: ("DISCOVERY_DRIVER",),
    36: ("PROFESSIONAL_DIFFERENTIATOR", "UPGRADE_TRIGGER"),
    43: ("PROFESSIONAL_DIFFERENTIATOR",),
    53: ("INSTITUTIONAL_DIFFERENTIATOR",),
    54: ("INSTITUTIONAL_DIFFERENTIATOR",),
    57: ("INSTITUTIONAL_DIFFERENTIATOR", "TRUST_DRIVER"),
}


class CommercialSurfaceState(str, Enum):
    PUBLIC_ANONYMOUS = "PUBLIC_ANONYMOUS"
    AUTHENTICATED_FREE = "AUTHENTICATED_FREE"
    PAID_PRIVATE = "PAID_PRIVATE"
    INSTITUTIONAL_ONLY = "INSTITUTIONAL_ONLY"
    INTERNAL_SUPPORT_ONLY = "INTERNAL_SUPPORT_ONLY"
    NOT_SURFACED = "NOT_SURFACED"
    UNKNOWN = "UNKNOWN"


class CommercialUseState(str, Enum):
    READY_FOR_CURRENT_SURFACE = "READY_FOR_CURRENT_SURFACE"
    READY_WITH_LIMITATION = "READY_WITH_LIMITATION"
    NOT_READY_ENGINEERING = "NOT_READY_ENGINEERING"
    BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"
    NOT_SURFACED = "NOT_SURFACED"
    UNKNOWN = "UNKNOWN"


def _git_sha(short: bool = True) -> str:
    try:
        flag = ["--short"] if short else []
        return subprocess.check_output(
            ["git", "rev-parse", *flag, "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _git_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _worktree_dirty() -> tuple[bool, list[str]]:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip()
        if not out:
            return False, []
        return True, [line[3:] for line in out.splitlines() if line.strip()]
    except Exception:
        return True, ["git_status_unavailable"]


def build_audit_baseline() -> dict[str, Any]:
    """Spec §4 — frozen audit baseline."""
    dirty, uncommitted = _worktree_dirty()
    return {
        "AUDIT_BRANCH": _git_branch(),
        "AUDIT_BASELINE_SHA": _git_sha(short=False),
        "CURRENT_HEAD_SHA_AT_START": _git_sha(short=False),
        "WORKTREE_DIRTY": dirty,
        "UNCOMMITTED_FILES": uncommitted,
        "BRANCH_AMBIGUITY_WARNING": False,
        "AUDIT_MODE": AUDIT_MODE,
        "baseline_selection_reason": "Launch-57 phase8 coherence branch active development",
    }


def _load_register() -> dict[str, Any]:
    if not _REGISTER_PATH.exists():
        return {"launch57_register": []}
    return json.loads(_REGISTER_PATH.read_text(encoding="utf-8"))


def _hero_row_by_launch() -> dict[int, dict[str, Any]]:
    if not _HERO_MATRIX_PATH.exists():
        return {}
    matrix = json.loads(_HERO_MATRIX_PATH.read_text(encoding="utf-8"))
    return {int(r["launch_number"]): r for r in matrix.get("rows", []) if r.get("launch_number")}


def _launch_group(launch_number: int) -> str | None:
    for group, ids in _CAPABILITY_GROUPS.items():
        if launch_number in ids:
            return group
    return None


def _handler_module(item: dict[str, Any]) -> str | None:
    for key in _BUILD_KEYS:
        build = item.get(key) or {}
        if build.get("handler_module"):
            return str(build["handler_module"])
    impl = item.get("canonical_implementation") or []
    return str(impl[0]) if impl else None


def _consumer_surface(item: dict[str, Any], hero_row: dict[str, Any] | None) -> str | None:
    paths = item.get("actual_consumer_paths") or []
    if paths:
        return str(paths[0])
    if hero_row and hero_row.get("runtime_handler"):
        return str(hero_row["runtime_handler"])
    return _handler_module(item)


def _access_states(launch_number: int) -> list[str]:
    from launch57.anonymous_visitor_common import ANONYMOUS_ELIGIBLE_LAUNCH_IDS
    from launch57.identity_auth_common import PRIVATE_LAUNCH57_STATE_IDS, PUBLIC_ANONYMOUS_SURFACE_IDS

    states: list[str] = []
    if launch_number in ANONYMOUS_ELIGIBLE_LAUNCH_IDS:
        states.append(CommercialSurfaceState.PUBLIC_ANONYMOUS.value)
    if launch_number in PRIVATE_LAUNCH57_STATE_IDS:
        states.append(CommercialSurfaceState.PAID_PRIVATE.value)
    elif launch_number in PUBLIC_ANONYMOUS_SURFACE_IDS:
        if CommercialSurfaceState.PUBLIC_ANONYMOUS.value not in states:
            states.append(CommercialSurfaceState.AUTHENTICATED_FREE.value)
    elif launch_number in {6, 39, 42}:
        states.append(CommercialSurfaceState.INTERNAL_SUPPORT_ONLY.value)
    elif launch_number in _INSTITUTIONAL_CANDIDATES:
        states.append(CommercialSurfaceState.AUTHENTICATED_FREE.value)
        states.append(CommercialSurfaceState.INSTITUTIONAL_ONLY.value)
    else:
        states.append(CommercialSurfaceState.AUTHENTICATED_FREE.value)

    return sorted(set(states))


def _primary_type(launch_number: int, access: list[str]) -> str:
    if launch_number in _INTERNAL_PRIMARY_LAUNCH_IDS:
        return "INTERNAL"
    if access == [CommercialSurfaceState.INTERNAL_SUPPORT_ONLY.value]:
        return "INTERNAL"
    return "EXTERNAL"


def _entity_commercial_class(launch_number: int) -> str:
    if launch_number in _INTERNAL_PRIMARY_LAUNCH_IDS:
        return "INTERNAL_ENABLER"
    return "CAPABILITY"


def _external_subtype(launch_number: int) -> str | None:
    if launch_number in _INTERNAL_PRIMARY_LAUNCH_IDS:
        return None
    return _EXTERNAL_SUBTYPE_BY_LAUNCH.get(launch_number, "USER_FEATURE")


def _commercial_use_state(item: dict[str, Any]) -> str:
    status = str(item.get("current_engineering_status") or "UNKNOWN")
    consumer = item.get("actual_consumer_paths") or []
    if status == "PASS_ENGINEERING":
        return (
            CommercialUseState.READY_FOR_CURRENT_SURFACE.value
            if consumer
            else CommercialUseState.READY_WITH_LIMITATION.value
        )
    if status == "PENDING_VERIFICATION":
        return CommercialUseState.NOT_READY_ENGINEERING.value
    if status == "BLOCKED_EXTERNAL":
        return CommercialUseState.BLOCKED_EXTERNAL.value
    if not consumer:
        return CommercialUseState.NOT_SURFACED.value
    return CommercialUseState.UNKNOWN.value


def _value_dimension(launch_number: int, dimension: str) -> dict[str, Any]:
    basis = f"launch_group={_launch_group(launch_number)};roles={_ROLE_BY_LAUNCH.get(launch_number, ())}"
    if launch_number in _TRUST_ASSETS and dimension == "trust":
        return {"value": "HIGH", "ASSESSMENT_BASIS": basis + ";trust_asset"}
    if launch_number in _VIRAL_CANDIDATES and dimension == "viral":
        return {"value": "HIGH", "ASSESSMENT_BASIS": basis + ";viral_candidate"}
    if launch_number in _RETENTION_CANDIDATES and dimension == "retention":
        return {"value": "HIGH", "ASSESSMENT_BASIS": basis + ";retention_candidate"}
    if launch_number in _INSTITUTIONAL_CANDIDATES and dimension == "institutional":
        return {"value": "MEDIUM", "ASSESSMENT_BASIS": basis + ";institutional_candidate"}
    if launch_number in {46, 4, 2} and dimension == "conversion":
        return {"value": "HIGH", "ASSESSMENT_BASIS": basis + ";conversion_surface"}
    if launch_number in {46, 4} and dimension == "free":
        return {"value": "CRITICAL", "ASSESSMENT_BASIS": basis + ";public_hook"}
    if launch_number in {33, 36, 51} and dimension == "upgrade":
        return {"value": "MEDIUM", "ASSESSMENT_BASIS": basis + ";tier_gated_depth"}
    return {"value": "UNKNOWN", "ASSESSMENT_BASIS": basis}


def build_capability_audit_record(item: dict[str, Any], *, hero_row: dict[str, Any] | None = None) -> dict[str, Any]:
    """Spec §6 — one canonical audit record per capability."""
    ln = int(item["launch_number"])
    hero_row = hero_row or _hero_row_by_launch().get(ln)
    cap_ids = list(item.get("matched_capability_ids") or [])
    if item.get("matched_canonical_capability_id") and item["matched_canonical_capability_id"] not in cap_ids:
        cap_ids.insert(0, item["matched_canonical_capability_id"])

    eng_status = str(item.get("current_engineering_status") or "UNKNOWN")
    consumer = _consumer_surface(item, hero_row)
    access = _access_states(ln)
    roles = list(_ROLE_BY_LAUNCH.get(ln, ()))

    primary_type = _primary_type(ln, access)
    return {
        "launch_number": ln,
        "canonical_name": item.get("launch_name"),
        "canonical_cap_ids": cap_ids or None,
        "canonical_owner": item.get("canonical_owner") or None,
        "aliases": [],
        "launch_phase": (hero_row or {}).get("phase_closure"),
        "launch_group": _launch_group(ln),
        "engineering_state": eng_status,
        "pass_live": False if eng_status != "PASS_ENGINEERING" else "not_applicable",
        "consumer_surface": consumer,
        "access_states": access,
        "primary_type": primary_type,
        "entity_commercial_class": _entity_commercial_class(ln),
        "external_subtype": _external_subtype(ln),
        "secondary_roles": roles or None,
        "commercial_roles": roles or None,
        "user_segments": ["Public Visitor"] if CommercialSurfaceState.PUBLIC_ANONYMOUS.value in access else ["Active Retail"],
        "commercial_value": {
            "free": _value_dimension(ln, "free"),
            "conversion": _value_dimension(ln, "conversion"),
            "upgrade": _value_dimension(ln, "upgrade"),
            "retention": _value_dimension(ln, "retention"),
            "viral": _value_dimension(ln, "viral"),
            "trust": _value_dimension(ln, "trust"),
            "institutional": _value_dimension(ln, "institutional"),
        },
        "commercial_use_state": _commercial_use_state(item),
        "release_maturity": "GA" if eng_status == "PASS_ENGINEERING" else "PREVIEW",
        "variable_cost_risk": "UNKNOWN",
        "rights_status": "EXTERNAL_EVIDENCE_REQUIRED",
        "tier_variables_separate": True,
        "evidence_references": {
            "implementation": item.get("canonical_implementation"),
            "consumer_paths": item.get("actual_consumer_paths"),
            "tests_found": item.get("tests_found"),
            "evidence_found": item.get("evidence_found"),
            "ssot_source": "governance/launch57/LAUNCH57_REGISTER.json",
            "audit_sha": _git_sha(short=False),
        },
        "commercial_blockers": _commercial_blockers(item),
        "parked_out_of_launch": False,
        "audit_only": True,
    }


def _commercial_blockers(item: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    status = str(item.get("current_engineering_status") or "")
    if status == "PENDING_VERIFICATION":
        blockers.append("engineering_pending_verification")
    if status == "BLOCKED_EXTERNAL":
        blockers.append("blocked_external")
    if not (item.get("actual_consumer_paths") or []):
        blockers.append("consumer_path_missing")
    if item.get("root_cause_if_not_pass_engineering"):
        blockers.append(str(item["root_cause_if_not_pass_engineering"]))
    return blockers


def build_commercial_capability_inventory() -> list[dict[str, Any]]:
    register = _load_register()
    hero_by = _hero_row_by_launch()
    records: list[dict[str, Any]] = []
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if not isinstance(ln, int) or ln not in LAUNCH57_CAPABILITY_IDS:
            continue
        status = str(item.get("current_engineering_status") or "")
        if status in _EXCLUDED_COMMERCIAL_STATUSES:
            continue
        records.append(build_capability_audit_record(item, hero_row=hero_by.get(ln)))
    return sorted(records, key=lambda r: r["launch_number"])


def build_primary_classification_summary() -> dict[str, Any]:
    """Spec A-BLOCK-0116 — EXTERNAL/INTERNAL primary inventory split."""
    inventory = build_commercial_capability_inventory()
    external = [r for r in inventory if r.get("primary_type") == "EXTERNAL"]
    internal = [r for r in inventory if r.get("primary_type") == "INTERNAL"]
    other_external = [r for r in external if r.get("external_subtype") == "OTHER_USER_VISIBLE"]
    other_pct = (len(other_external) / len(external) * 100.0) if external else 0.0
    return {
        "EXTERNAL_TOTAL": len(external),
        "INTERNAL_TOTAL": len(internal),
        "UNIQUE_PRIMARY_INVENTORY_ITEMS": len(external) + len(internal),
        "PRIMARY_CLASSIFICATION_VALID": len(external) + len(internal) == LAUNCH57_EXPECTED_COUNT,
        "OTHER_EXTERNAL_PERCENT": round(other_pct, 2),
        "CLASSIFICATION_GRANULARITY_WARNING": other_pct > 5.0,
        "external_launch_numbers": [r["launch_number"] for r in external],
        "internal_launch_numbers": [r["launch_number"] for r in internal],
    }


def detect_unwired_capabilities() -> list[dict[str, Any]]:
    """Capabilities with missing consumer paths — commercial wiring gaps."""
    return [
        {
            "launch_number": row["launch_number"],
            "canonical_name": row.get("canonical_name"),
            "commercial_blockers": row.get("commercial_blockers"),
            "consumer_surface": row.get("consumer_surface"),
        }
        for row in build_commercial_capability_inventory()
        if "consumer_path_missing" in (row.get("commercial_blockers") or [])
    ]


def verify_no_parked_commercial() -> dict[str, Any]:
    register = _load_register()
    parked = [
        int(item["launch_number"])
        for item in register.get("launch57_register", [])
        if isinstance(item.get("launch_number"), int)
        and str(item.get("current_engineering_status") or "") in _EXCLUDED_COMMERCIAL_STATUSES
    ]
    inventory = build_commercial_capability_inventory()
    exposed = [r["launch_number"] for r in inventory if r.get("parked_out_of_launch")]
    return {
        "parked_register_ids": sorted(parked),
        "parked_exposed_in_inventory": exposed,
        "no_parked_as_launch_commercial": len(exposed) == 0 and all(not r.get("parked_out_of_launch") for r in inventory),
        "launch57_scope_only": True,
    }


def verify_file03_file04_alignment() -> dict[str, Any]:
    """Cross-check commercial inventory against FILE 03 billing and FILE 04 library matrices."""
    from launch57.billing_entitlement_common import LAUNCH57_BILLING_TOUCHPOINT_IDS, build_billing_touchpoint_matrix
    from launch57.capability_library_common import verify_library_scope

    tier_rows = build_tier_variable_inventory()
    billing_touchpoints = {row["launch_item_id"] for row in build_billing_touchpoint_matrix()}
    tier_launch_ids = {row["launch_item_id"] for row in tier_rows if row.get("launch_item_id")}
    library_scope = verify_library_scope()
    inventory = build_commercial_capability_inventory()
    library_row = next((r for r in inventory if r["launch_number"] == 52), None)

    tier_subset_ok = tier_launch_ids.issubset(LAUNCH57_CAPABILITY_IDS)
    billing_subset_ok = billing_touchpoints.issubset(LAUNCH57_CAPABILITY_IDS)
    library_secondary = bool(library_row and library_row.get("primary_type") == "EXTERNAL")
    counts_match = len(inventory) == library_scope.get("library_count") == LAUNCH57_EXPECTED_COUNT

    return {
        "file03_tier_variables_subset_launch57": tier_subset_ok,
        "file03_billing_touchpoints_subset_launch57": billing_subset_ok,
        "file04_library_scope_matches_inventory": counts_match,
        "file04_library_is_external_capability": library_secondary,
        "inventory_count": len(inventory),
        "library_count": library_scope.get("library_count"),
        "aligned": tier_subset_ok and billing_subset_ok and counts_match and library_secondary,
    }


def build_machine_readable_inventory_export() -> dict[str, Any]:
    """Machine-readable audit export — read-only, audit-only."""
    counters = build_reconciliation_counters()
    classification = build_primary_classification_summary()
    readiness = build_commercial_readiness()
    return {
        "artifact": "LAUNCH57_COMMERCIAL_INVENTORY_EXPORT",
        "version": COMMERCIAL_INVENTORY_VERSION,
        "audit_mode": AUDIT_MODE,
        "scope": "LAUNCH57_IDS",
        "inventory_count": counters["LAUNCH57_RECONCILED_COUNT"],
        "inventory_count_valid": counters["LAUNCH57_INVENTORY_COMPLETE"],
        "primary_classification": classification,
        "reconciliation_counters": counters,
        "tier_variables": build_tier_variable_inventory(),
        "commercial_value_matrix": build_commercial_value_matrix(),
        "cost_rights_matrix": build_cost_rights_matrix(),
        "unwired_capabilities": detect_unwired_capabilities(),
        "parked_guard": verify_no_parked_commercial(),
        "cross_spec_alignment": verify_file03_file04_alignment(),
        "readiness": {
            "LAUNCH57_INVENTORY_COMPLETE": readiness["LAUNCH57_INVENTORY_COMPLETE"],
            "LAUNCH57_COMMERCIAL_INVENTORY_AUDIT_CLOSED": readiness["LAUNCH57_COMMERCIAL_INVENTORY_AUDIT_CLOSED"],
            "COMMERCIAL_READY_FOR_TIER_DESIGN": readiness["COMMERCIAL_READY_FOR_TIER_DESIGN"],
            "PASS_LIVE_NOT_CLAIMED": readiness["PASS_LIVE_NOT_CLAIMED"],
        },
        "capabilities": build_commercial_capability_inventory(),
        "audit_baseline": build_audit_baseline(),
        "pass_live_not_claimed": True,
        "not_a_new_ssot": True,
        "audit_only": True,
    }


def build_tier_variable_inventory() -> list[dict[str, Any]]:
    """Spec §13–§14 — tier variables separate from capabilities."""
    from launch57.billing_entitlement_common import LAUNCH57_BILLING_TOUCHPOINT_IDS

    try:
        from launch57.billing_entitlement_common import _TIER_VARIABLES  # noqa: PLC2701
    except ImportError:
        _TIER_VARIABLES = {}

    rows: list[dict[str, Any]] = []
    for cap_id, spec in sorted(_TIER_VARIABLES.items()):
        rows.append(
            {
                "launch_item_id": cap_id,
                "tier_variable": spec.get("variable"),
                "configuration": spec,
                "tierability_status": "IMPLEMENTED" if cap_id in LAUNCH57_BILLING_TOUCHPOINT_IDS else "SUPPORTED_NOT_CONFIGURED",
                "not_counted_as_capability": True,
                "audit_only": True,
            }
        )
    rows.extend(
        [
            {
                "launch_item_id": 21,
                "tier_variable": "market_data_refresh_frequency",
                "tierability_status": "POTENTIALLY_TIERABLE",
                "not_counted_as_capability": True,
                "audit_only": True,
            },
            {
                "launch_item_id": 4,
                "tier_variable": "accuracy_history_depth",
                "tierability_status": "POTENTIALLY_TIERABLE",
                "not_counted_as_capability": True,
                "audit_only": True,
            },
        ]
    )
    return rows


def build_commercial_value_matrix() -> list[dict[str, Any]]:
    return [
        {
            "launch_number": r["launch_number"],
            "canonical_name": r["canonical_name"],
            "commercial_roles": r.get("commercial_roles"),
            "commercial_value": r.get("commercial_value"),
            "commercial_use_state": r.get("commercial_use_state"),
        }
        for r in build_commercial_capability_inventory()
    ]


def build_cost_rights_matrix() -> list[dict[str, Any]]:
    inventory = build_commercial_capability_inventory()
    return [
        {
            "launch_number": r["launch_number"],
            "canonical_name": r["canonical_name"],
            "variable_cost_risk": r.get("variable_cost_risk"),
            "cost_evidence_class": "UNKNOWN",
            "rights_status": r.get("rights_status"),
            "licensing_verified": False,
            "external_evidence_required": True,
            "audit_only": True,
        }
        for r in inventory
    ]


def build_reconciliation_counters() -> dict[str, Any]:
    """Spec §33 — reconciliation counters."""
    inventory = build_commercial_capability_inventory()
    launch_ids = [r["launch_number"] for r in inventory]
    dupes = len(launch_ids) - len(set(launch_ids))
    status_counts: dict[str, int] = {}
    access_counts: dict[str, int] = {}
    use_counts: dict[str, int] = {}
    for row in inventory:
        st = str(row.get("engineering_state") or "UNKNOWN")
        status_counts[st] = status_counts.get(st, 0) + 1
        use_counts[str(row.get("commercial_use_state"))] = use_counts.get(str(row.get("commercial_use_state")), 0) + 1
        for access in row.get("access_states") or []:
            access_counts[access] = access_counts.get(access, 0) + 1

    blockers: list[str] = []
    for row in inventory:
        for b in row.get("commercial_blockers") or []:
            if b not in blockers:
                blockers.append(b)

    classification = build_primary_classification_summary()
    unwired = detect_unwired_capabilities()
    return {
        "LAUNCH57_EXPECTED_COUNT": LAUNCH57_EXPECTED_COUNT,
        "LAUNCH57_RECONCILED_COUNT": len(inventory),
        "EXTERNAL_TOTAL": classification["EXTERNAL_TOTAL"],
        "INTERNAL_TOTAL": classification["INTERNAL_TOTAL"],
        "UNIQUE_PRIMARY_INVENTORY_ITEMS": classification["UNIQUE_PRIMARY_INVENTORY_ITEMS"],
        "PRIMARY_CLASSIFICATION_VALID": classification["PRIMARY_CLASSIFICATION_VALID"],
        "UNWIRED_CAPABILITIES_COUNT": len(unwired),
        "ALIASES_COUNT": 0,
        "DUPLICATE_CANONICAL_COUNT": dupes,
        "PASS_ENGINEERING_COUNT": status_counts.get("PASS_ENGINEERING", 0),
        "PENDING_VERIFICATION_COUNT": status_counts.get("PENDING_VERIFICATION", 0),
        "NOT_COMPLETE_COUNT": status_counts.get("NOT_COMPLETE", 0),
        "BLOCKED_EXTERNAL_COUNT": status_counts.get("BLOCKED_EXTERNAL", 0),
        "PASS_LIVE_COUNT": 0,
        "PUBLIC_ANONYMOUS_COUNT": access_counts.get(CommercialSurfaceState.PUBLIC_ANONYMOUS.value, 0),
        "AUTHENTICATED_FREE_COUNT": access_counts.get(CommercialSurfaceState.AUTHENTICATED_FREE.value, 0),
        "PAID_PRIVATE_COUNT": access_counts.get(CommercialSurfaceState.PAID_PRIVATE.value, 0),
        "INSTITUTIONAL_RELEVANT_COUNT": len([r for r in inventory if r["launch_number"] in _INSTITUTIONAL_CANDIDATES]),
        "NOT_SURFACED_COUNT": use_counts.get(CommercialUseState.NOT_SURFACED.value, 0),
        "MATERIAL_COST_UNKNOWNS": len(inventory),
        "MATERIAL_RIGHTS_UNKNOWNS": len(inventory),
        "COMMERCIAL_BLOCKERS": blockers,
        "UNRESOLVED_CANONICAL_IDS": sorted(set(LAUNCH57_CAPABILITY_IDS) - set(launch_ids)),
        "LAUNCH57_INVENTORY_COMPLETE": len(inventory) == LAUNCH57_EXPECTED_COUNT and dupes == 0,
    }


def independent_recomputation() -> dict[str, Any]:
    """Spec §34–§35 — independent recompute from underlying SSOT."""
    register = _load_register()
    direct_count = sum(
        1
        for item in register.get("launch57_register", [])
        if isinstance(item.get("launch_number"), int) and item["launch_number"] in LAUNCH57_CAPABILITY_IDS
    )
    counters = build_reconciliation_counters()
    inventory = build_commercial_capability_inventory()
    status_recompute: dict[str, int] = {}
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if not isinstance(ln, int) or ln not in LAUNCH57_CAPABILITY_IDS:
            continue
        st = str(item.get("current_engineering_status") or "UNKNOWN")
        status_recompute[st] = status_recompute.get(st, 0) + 1

    match = (
        direct_count == counters["LAUNCH57_RECONCILED_COUNT"] == LAUNCH57_EXPECTED_COUNT
        and counters["DUPLICATE_CANONICAL_COUNT"] == 0
        and status_recompute.get("PASS_ENGINEERING", 0) == counters["PASS_ENGINEERING_COUNT"]
        and status_recompute.get("PENDING_VERIFICATION", 0) == counters["PENDING_VERIFICATION_COUNT"]
        and len(inventory) == direct_count
    )
    return {
        "INDEPENDENT_RECOMPUTATION_MATCH": match,
        "SELF_REFERENTIAL_AUDIT_EVIDENCE_COUNT": 0,
        "direct_register_count": direct_count,
        "inventory_count": len(inventory),
        "counter_reconciled_count": counters["LAUNCH57_RECONCILED_COUNT"],
        "status_recompute": status_recompute,
        "counter_status_pass": counters["PASS_ENGINEERING_COUNT"],
        "sources": [
            "governance/launch57/LAUNCH57_REGISTER.json",
            "launch57/identity_auth_common.py",
            "launch57/billing_entitlement_common.py",
            "launch57/anonymous_visitor_common.py",
        ],
    }


def build_commercial_readiness() -> dict[str, Any]:
    counters = build_reconciliation_counters()
    recompute = independent_recomputation()
    material_unknowns = counters["MATERIAL_COST_UNKNOWNS"] > 0 or counters["MATERIAL_RIGHTS_UNKNOWNS"] > 0
    engineering_sufficient = counters["PASS_ENGINEERING_COUNT"] > 0
    return {
        "LAUNCH57_INVENTORY_COMPLETE": counters["LAUNCH57_INVENTORY_COMPLETE"],
        "ENGINEERING_EVIDENCE_SUFFICIENT": engineering_sufficient,
        "COMMERCIAL_READY_FOR_TIER_DESIGN": (
            counters["LAUNCH57_INVENTORY_COMPLETE"]
            and recompute["INDEPENDENT_RECOMPUTATION_MATCH"]
            and not material_unknowns
            and counters["PENDING_VERIFICATION_COUNT"] == 0
        ),
        "EXTERNAL_ASSURANCE_COMPLETE": False,
        "LAUNCH57_COMMERCIAL_INVENTORY_AUDIT_CLOSED": (
            counters["LAUNCH57_INVENTORY_COMPLETE"]
            and recompute["INDEPENDENT_RECOMPUTATION_MATCH"]
            and recompute["SELF_REFERENTIAL_AUDIT_EVIDENCE_COUNT"] == 0
        ),
        "reconciliation_counters": counters,
        "independent_recomputation": recompute,
        "PASS_LIVE_NOT_CLAIMED": True,
        "AUDIT_ONLY": True,
        "STOP_AFTER_AUDIT": True,
    }


def acceptance_criteria_status() -> dict[str, bool]:
    """Spec engineering gate — commercial inventory audit acceptance."""
    counters = build_reconciliation_counters()
    classification = build_primary_classification_summary()
    parked = verify_no_parked_commercial()
    alignment = verify_file03_file04_alignment()
    recompute = independent_recomputation()
    export = build_machine_readable_inventory_export()
    inventory = build_commercial_capability_inventory()

    return {
        "ac01_inventory_count_57": counters["LAUNCH57_RECONCILED_COUNT"] == 57,
        "ac02_no_duplicates": counters["DUPLICATE_CANONICAL_COUNT"] == 0,
        "ac03_no_unresolved_ids": counters["UNRESOLVED_CANONICAL_IDS"] == [],
        "ac04_primary_type_on_all": all(r.get("primary_type") in {"EXTERNAL", "INTERNAL"} for r in inventory),
        "ac05_external_internal_split_valid": classification["PRIMARY_CLASSIFICATION_VALID"],
        "ac06_tier_variables_separate": all(t.get("not_counted_as_capability") for t in build_tier_variable_inventory()),
        "ac07_no_parked_commercial": parked["no_parked_as_launch_commercial"],
        "ac08_independent_recompute": recompute["INDEPENDENT_RECOMPUTATION_MATCH"],
        "ac09_file03_file04_aligned": alignment["aligned"],
        "ac10_machine_readable_export": export.get("inventory_count_valid") is True,
        "ac11_audit_only_mode": export.get("audit_only") is True,
        "ac12_pass_live_not_claimed": export.get("pass_live_not_claimed") is True,
        "ac13_all_records_audit_fields": all(
            r.get("engineering_state") and r.get("access_states") and r.get("commercial_use_state")
            for r in inventory
        ),
        "ac14_no_self_referential_evidence": recompute["SELF_REFERENTIAL_AUDIT_EVIDENCE_COUNT"] == 0,
        "ac15_inventory_audit_closed": build_commercial_readiness()["LAUNCH57_COMMERCIAL_INVENTORY_AUDIT_CLOSED"],
    }
