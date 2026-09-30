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

_IMPLEMENTED = frozenset(f"AIE-{n:03d}" for n in range(1, 9))
_PARTIAL = frozenset(f"AIE-{n:03d}" for n in range(9, 21))


def aie_catalog() -> list[dict[str, Any]]:
    rows = []
    for eid in sorted(_AIE_TITLES.keys(), key=lambda x: int(x.split("-")[1])):
        if eid in _IMPLEMENTED:
            status = "IMPLEMENTED"
        elif eid in _PARTIAL:
            status = "PARTIAL"
        else:
            status = "SPEC_ONLY"
        rows.append({"requirement_id": eid, "status": status, "title": _AIE_TITLES[eid], "bgs": _BGS})
    return rows


def aie_summary() -> dict[str, Any]:
    rows = aie_catalog()
    return build_summary(domain="AIE", bgs=_BGS, rows=rows, honest_min_implemented=5, strict_min_implemented=12)


def verify_aie_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(aie_catalog(), requirement_id)


def verify_aie_runtime() -> dict[str, Any]:
    status = adaptive_ux_status()
    return {
        "six_heroes_count": len(status.get("six_heroes", SIX_HEROES)),
        "heroes_router": status.get("heroes_router"),
        "all_requirements": verify_all_requirements(aie_catalog()),
    }
