"""TZ-001→036 global timezone requirement spine (BGS-007)."""

from __future__ import annotations

from typing import Any

from governance.spine_base import build_catalog, build_summary, verify_all_requirements, verify_requirement
from governance.timezone_governance import timezone_status

_PREFIX = "TZ-"
_BGS = "BGS-007"

_IMPLEMENTED = frozenset(f"{_PREFIX}{n:03d}" for n in range(1, 8))
_PARTIAL = frozenset(f"{_PREFIX}{n:03d}" for n in range(8, 37))


def tz_catalog() -> list[dict[str, Any]]:
    return build_catalog(prefix=_PREFIX, bgs=_BGS, implemented=_IMPLEMENTED, partial=_PARTIAL, max_num=36)


def tz_summary() -> dict[str, Any]:
    rows = tz_catalog()
    return build_summary(domain="TZ", bgs=_BGS, rows=rows, honest_min_implemented=5, strict_min_implemented=20)


def verify_tz_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(tz_catalog(), requirement_id)


def verify_tz_runtime() -> dict[str, Any]:
    status = timezone_status()
    return {
        "iana_available": status.get("iana_available"),
        "canonical_storage": status.get("canonical_storage"),
        "all_requirements": verify_all_requirements(tz_catalog()),
    }
