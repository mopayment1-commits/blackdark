"""AIE-001→020 adaptive intelligence experience requirement spine (BGS-004)."""

from __future__ import annotations

from typing import Any

from governance.adaptive_ux_governance import SIX_HEROES, adaptive_ux_status
from governance.spine_base import build_summary, verify_all_requirements, verify_requirement

_BGS = "BGS-004"

_AIE_TITLES = {
    "AIE-001": "Six Heroes primary surfaces",
    "AIE-002": "Intelligence Router contract",
    "AIE-003": "Calm Surface doctrine",
    "AIE-004": "Universal Command",
    "AIE-005": "Today Focus surface",
    "AIE-006": "Decision Contract UX",
    "AIE-007": "Evidence and Trust views",
    "AIE-008": "Capability Explorer",
    "AIE-009": "Intent and Context Resolver",
    "AIE-010": "Playbook selection",
    "AIE-011": "Hero typed edges",
    "AIE-012": "Operational Intelligence workspace",
    "AIE-013": "Router selection contract",
    "AIE-014": "Sellable UX core P1",
    "AIE-015": "My Stack summary",
    "AIE-016": "Top Opportunity surface",
    "AIE-017": "Key Risk surface",
    "AIE-018": "What Changed surface",
    "AIE-019": "Institutional Data Room link",
    "AIE-020": "Adaptive surface gating",
}

_AIE_RUNTIME_CHECKS: dict[str, str] = {
    "AIE-001": "heroes_router",
    "AIE-002": "router_runtime",
    "AIE-003": "calm_surface",
    "AIE-004": "adaptive_api",
    "AIE-005": "adaptive_api",
    "AIE-006": "decision_contract",
    "AIE-007": "trust_pulse",
    "AIE-008": "adaptive_api",
    "AIE-009": "router_runtime",
    "AIE-010": "adaptive_api",
    "AIE-011": "adaptive_api",
    "AIE-012": "adaptive_api",
    "AIE-013": "router_runtime",
    "AIE-014": "calm_surface",
    "AIE-015": "adaptive_api",
    "AIE-016": "adaptive_api",
    "AIE-017": "adaptive_api",
    "AIE-018": "adaptive_api",
    "AIE-019": "adaptive_api",
    "AIE-020": "adaptive_api",
}


def _runtime_ok(status: dict[str, Any], requirement_id: str) -> bool:
    key = _AIE_RUNTIME_CHECKS.get(requirement_id)
    if not key:
        return False
    bindings = status.get("bindings") or {}
    if key in bindings:
        return bool(bindings[key])
    return bool(status.get(key))


def aie_catalog() -> list[dict[str, Any]]:
    status = adaptive_ux_status()
    rows = []
    for eid in sorted(_AIE_TITLES.keys(), key=lambda x: int(x.split("-")[1])):
        if _runtime_ok(status, eid):
            impl_status = "IMPLEMENTED"
        else:
            impl_status = "PARTIAL"
        rows.append({"requirement_id": eid, "status": impl_status, "title": _AIE_TITLES[eid], "bgs": _BGS})
    return rows


def aie_summary() -> dict[str, Any]:
    rows = aie_catalog()
    return build_summary(domain="AIE", bgs=_BGS, rows=rows, honest_min_implemented=5, strict_min_implemented=12)


def verify_aie_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(aie_catalog(), requirement_id)


def verify_aie_runtime() -> dict[str, Any]:
    status = adaptive_ux_status()
    catalog = aie_catalog()
    implemented = sum(1 for r in catalog if r["status"] == "IMPLEMENTED")
    return {
        "six_heroes_count": len(status.get("six_heroes", SIX_HEROES)),
        "heroes_router": status.get("heroes_router"),
        "adaptive_api": status.get("adaptive_api"),
        "bindings": status.get("bindings"),
        "implemented_count": implemented,
        "total": len(catalog),
        "all_requirements": verify_all_requirements(catalog),
    }
