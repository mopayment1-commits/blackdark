"""ERR-001→050 failure/degraded mode requirement spine (BGS-008)."""

from __future__ import annotations

from typing import Any

from governance.failure_governance import failure_governance_status
from governance.spine_base import build_catalog, build_summary, verify_all_requirements, verify_requirement

_PREFIX = "ERR-"
_BGS = "BGS-008"
_SPEC = "governing-sources-population/BLACKDARK_INSTITUTIONAL_FAILURE_DEGRADED_MODE_ERROR_MESSAGING_RECOVERY_SPEC_v1(1).md"

_IMPLEMENTED = frozenset(f"{_PREFIX}{n:03d}" for n in range(1, 11))
_PARTIAL = frozenset(f"{_PREFIX}{n:03d}" for n in range(11, 51))


def err_catalog() -> list[dict[str, Any]]:
    return build_catalog(
        prefix=_PREFIX,
        bgs=_BGS,
        implemented=_IMPLEMENTED,
        partial=_PARTIAL,
        max_num=50,
        title_source=_SPEC,
        section_pattern=r"^## (ERR-\d+) — (.+)$",
    )


def err_summary() -> dict[str, Any]:
    rows = err_catalog()
    return build_summary(domain="ERR", bgs=_BGS, rows=rows, honest_min_implemented=8, strict_min_implemented=25)


def verify_err_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(err_catalog(), requirement_id)


def verify_err_runtime() -> dict[str, Any]:
    status = failure_governance_status()
    return {
        "rfc9457": status.get("rfc9457_problem_contract"),
        "five_layer_ux": status.get("five_layer_ux"),
        "all_requirements": verify_all_requirements(err_catalog()),
    }
