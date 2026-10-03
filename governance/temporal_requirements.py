"""TIE-001→020 temporal intelligence requirement spine (BGS-003)."""

from __future__ import annotations

from typing import Any

from governance.spine_base import build_catalog, build_summary, verify_all_requirements, verify_requirement
from governance.temporal_governance import temporal_governance_status

_PREFIX = "TIE-"
_BGS = "BGS-003"

_TIE_TITLES = {
    "TIE-001": "Evidence acceleration spine",
    "TIE-002": "Point-in-time reconstruction",
    "TIE-003": "Feed lag detection",
    "TIE-004": "Stale data guard",
    "TIE-005": "Replay bootstrap",
    "TIE-006": "Hot tier evidence",
    "TIE-007": "Warm tier evidence",
    "TIE-008": "Cold tier evidence",
    "TIE-009": "Leakage firewall",
    "TIE-010": "Internal P1 mode",
    "TIE-011": "User-facing P2 mode",
    "TIE-012": "Representative sampling stream",
    "TIE-013": "High-information learning stream",
    "TIE-014": "Temporal provenance chain",
    "TIE-015": "Evidence freshness SLA",
    "TIE-016": "Cross-time reconciliation",
    "TIE-017": "Outcome attribution window",
    "TIE-018": "Acceleration metrics",
    "TIE-019": "P0 build spine",
    "TIE-020": "P1 build spine",
}

_IMPLEMENTED = frozenset(f"TIE-{n:03d}" for n in range(1, 9))
_PARTIAL = frozenset(f"TIE-{n:03d}" for n in range(9, 21))


def _tie_catalog_rows() -> list[dict[str, Any]]:
    rows = []
    for eid in sorted(_TIE_TITLES.keys(), key=lambda x: int(x.split("-")[1])):
        if eid in _IMPLEMENTED:
            status = "IMPLEMENTED"
        elif eid in _PARTIAL:
            status = "PARTIAL"
        else:
            status = "SPEC_ONLY"
        rows.append({"requirement_id": eid, "status": status, "title": _TIE_TITLES[eid], "bgs": _BGS})
    return rows


def tie_catalog() -> list[dict[str, Any]]:
    return _tie_catalog_rows()


def tie_summary() -> dict[str, Any]:
    rows = tie_catalog()
    return build_summary(domain="TIE", bgs=_BGS, rows=rows, honest_min_implemented=5, strict_min_implemented=12)


def verify_tie_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(tie_catalog(), requirement_id)


def verify_tie_runtime() -> dict[str, Any]:
    status = temporal_governance_status()
    return {
        "feed_lag_scanner": status.get("feed_lag_scanner"),
        "replay_bootstrap": status.get("replay_bootstrap"),
        "all_requirements": verify_all_requirements(tie_catalog()),
    }
