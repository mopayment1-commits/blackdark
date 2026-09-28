"""DSR-001→024 data/storage v4 requirement spine (BGS-002)."""

from __future__ import annotations

from typing import Any

from governance.spine_base import build_catalog, build_summary, verify_all_requirements, verify_requirement
from governance.storage_governance import storage_governance_status

_PREFIX = "DSR-"
_BGS = "BGS-002"

_IMPLEMENTED = frozenset(f"{_PREFIX}{n:03d}" for n in range(1, 10))
_PARTIAL = frozenset(f"{_PREFIX}{n:03d}" for n in range(10, 25))


def dsr_catalog() -> list[dict[str, Any]]:
    return build_catalog(prefix=_PREFIX, bgs=_BGS, implemented=_IMPLEMENTED, partial=_PARTIAL, max_num=24)


def dsr_summary() -> dict[str, Any]:
    rows = dsr_catalog()
    return build_summary(domain="DSR", bgs=_BGS, rows=rows, honest_min_implemented=5, strict_min_implemented=15)


def verify_dsr_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(dsr_catalog(), requirement_id)


def verify_dsr_runtime() -> dict[str, Any]:
    status = storage_governance_status()
    return {
        "tier_orchestrator": status.get("tier_orchestrator"),
        "dsr_export_erase": status.get("dsr_export_erase"),
        "all_requirements": verify_all_requirements(dsr_catalog()),
    }
